from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth.models import User
from spyglassserver import models
from spyglassserver.views.views_pdf_analysis import views_pdf_analysis as vpa
from django.conf import settings
import os
import requests
import json
from spyglassserver.views.chat_model import text_extraction
from spyglassserver.views.chat_model import retrieval

@api_view(["GET"])
def sayHello(request):
    return JsonResponse({"message": "Hello World!"})


def download_pdf_from_s3(presigned_url, output_file_path):
    try:
        response = requests.get(presigned_url, stream=True)
        response.raise_for_status()  # Ensure we got a valid response
        with open(output_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        # print(f"PDF downloaded successfully: {output_file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download PDF: {e}")
        
        
def get_research_paper_details_from_doi(doi):
    research_paper_obj = models.ResearchPaper.objects.filter(doi=doi).values().first()
    research_paper_obj['ref_docs'] = json.loads(research_paper_obj['ref_docs']) if research_paper_obj['ref_docs'] else []
    return research_paper_obj


@api_view(["GET"])  
def get_research_paper_details(request):
    pdf_url = request.GET.get("pdf_url")
    if not pdf_url:
        return JsonResponse({"error": "pdf_url parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    pdfFileName = request.GET.get("filename")
    user_email = request.GET.get("user_id")
    # pdfFileName = "k.pdf"
    user_path = os.path.join(settings.BASE_DIR, "Data", user_email)
    if not os.path.exists(user_path):
        os.makedirs(user_path, exist_ok=True)
    pdf_path = os.path.join(settings.BASE_DIR, "Data", user_email, "research_paper")
    if not os.path.exists(pdf_path):
        os.makedirs(pdf_path, exist_ok=True)
    pdf_path = os.path.join(pdf_path, pdfFileName)
    
    # Check if the file already exists
    if os.path.exists(pdf_path):
        print(f"File already exists: {pdf_path}")
    else:
        download_pdf_from_s3(pdf_url, pdf_path)
        
    doi = vpa.get_doi_from_pdf(pdf_path)
    doc_id = doi.replace("/", "@") if doi else None
    print(f"Extracted DOI: {doi}")
    pdf_vector_store_path = os.path.join(settings.BASE_DIR, "Data", user_email, "vector_store", doc_id)
    if not os.path.exists(pdf_vector_store_path):
        text_extraction.process_new_document(user_path=user_path, pdf_path=pdf_path, doc_id=doc_id)
    # doi = "10.1080/15376494.2021.2014002"
    research_paper_details = get_research_paper_details_from_doi(doi)
    if research_paper_details:
        return JsonResponse({"research_paper_details": research_paper_details})
    else:
        return JsonResponse({"error": "Research paper not found."})        
    
    
@api_view(["POST"])
def generate_query_response(request):
    query = request.data.get("query")
    pdf_name = request.data.get("pdf_name")
    user_email = request.data.get("user_email")
    
    print(f"Received query: ==========> {query}, pdf_name: {pdf_name}, user_email: {user_email}")
    
    if not query or not pdf_name or not user_email:
        return JsonResponse({"error": "query, pdf_name, and user_id parameters are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    pdf_path = os.path.join(settings.BASE_DIR, "Data", user_email, "research_paper", pdf_name)
    doi = vpa.get_doi_from_pdf(pdf_path)
    if not doi:
        return JsonResponse({"error": "DOI not found in the PDF."}, status=status.HTTP_400_BAD_REQUEST)
    doi = doi.replace("/", "@")
    pdf_vector_path = os.path.join(settings.BASE_DIR, "Data", user_email, "vector_store", doi)
    
    query_response = retrieval.get_document_answer(query=query, vector_store_dir=pdf_vector_path, user_id=user_email, doc_id=doi, max_length=1000)
    
    return JsonResponse(query_response, status=status.HTTP_200_OK)