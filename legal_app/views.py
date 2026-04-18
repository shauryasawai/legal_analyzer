import json
import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import DocumentAnalysis, Clause
from .langchain_service import (
    extract_text, store_document_chunks,
    analyze_document, generate_eli5,
)

logger = logging.getLogger(__name__)


def index(request):
    """Landing page with upload form."""
    recent_docs = DocumentAnalysis.objects.filter(status='done')[:5]
    return render(request, 'legal_app/index.html', {'recent_docs': recent_docs})


def analysis_view(request, doc_id):
    """Show analysis results for a document."""
    doc = get_object_or_404(DocumentAnalysis, id=doc_id)
    clauses = doc.clauses.all()

    risk_counts = {
        'high': clauses.filter(risk_level='high').count(),
        'medium': clauses.filter(risk_level='medium').count(),
        'low': clauses.filter(risk_level='low').count(),
    }

    return render(request, 'legal_app/analysis.html', {
        'doc': doc,
        'clauses': clauses,
        'risk_counts': risk_counts,
        'total': clauses.count(),
    })


@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """Handle file upload and trigger analysis."""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    uploaded_file = request.FILES['file']
    allowed_types = ['.pdf', '.docx', '.doc', '.txt']
    filename = uploaded_file.name.lower()

    if not any(filename.endswith(ext) for ext in allowed_types):
        return JsonResponse({'error': 'Only PDF, DOCX, and TXT files are supported'}, status=400)

    if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB limit
        return JsonResponse({'error': 'File too large (max 10 MB)'}, status=400)

    # Save document record
    doc = DocumentAnalysis.objects.create(
        filename=uploaded_file.name,
        file=uploaded_file,
        status='processing',
    )

    try:
        # Extract text
        full_text = extract_text(doc.file.path)
        if not full_text.strip():
            raise ValueError("No text could be extracted from this file")

        doc.full_text = full_text
        doc.status = 'processing'
        doc.save()

        # Store in vector DB
        store_document_chunks(
            full_text,
            str(doc.id),
            str(settings.VECTORSTORE_PATH),
        )

        # Analyze with Claude
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        clauses_data = analyze_document(full_text, api_key)

        # Save clauses
        for i, clause_data in enumerate(clauses_data):
            Clause.objects.create(
                document=doc,
                title=clause_data.get('title', f'Clause {i+1}'),
                original_text=clause_data.get('original_text', ''),
                simplified_text=clause_data.get('simplified_text', ''),
                risk_level=clause_data.get('risk_level', 'low'),
                risk_reason=clause_data.get('risk_reason', ''),
                clause_type=clause_data.get('clause_type', ''),
                order=i,
            )

        doc.status = 'done'
        doc.save()

        return JsonResponse({
            'success': True,
            'doc_id': str(doc.id),
            'redirect': f'/analysis/{doc.id}/',
        })

    except Exception as e:
        logger.error(f"Analysis failed for doc {doc.id}: {e}")
        doc.status = 'error'
        doc.save()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def eli5_clause(request, clause_id):
    """Generate ELI5 explanation for a specific clause."""
    clause = get_object_or_404(Clause, id=clause_id)

    # Return cached ELI5 if already generated
    if clause.eli5_text:
        return JsonResponse({'eli5': clause.eli5_text})

    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return JsonResponse({'error': 'API key not configured'}, status=500)

    eli5 = generate_eli5(clause.original_text, api_key)
    clause.eli5_text = eli5
    clause.save()

    return JsonResponse({'eli5': eli5})


@require_http_methods(["GET"])
def api_status(request, doc_id):
    """Poll document processing status."""
    doc = get_object_or_404(DocumentAnalysis, id=doc_id)
    return JsonResponse({
        'status': doc.status,
        'clause_count': doc.clauses.count(),
    })
