from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework import status
from django.contrib.auth.models import User
from spyglassserver import models
from spyglassserver.views_pdf_analysis import views_pdf_analysis as vpa
from django.conf import settings
import os
import requests
import json

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
    # pdfFileName = "k.pdf"
    pdf_path = os.path.join(settings.BASE_DIR, "Data", "research_paper")
    pdf_path = os.path.join(pdf_path, pdfFileName)
    
    # Check if the file already exists
    if os.path.exists(pdf_path):
        print(f"File already exists: {pdf_path}")
    else:
        download_pdf_from_s3(pdf_url, pdf_path)
        
    doi = vpa.get_doi_from_pdf(pdf_path)
    # doi = "10.1080/15376494.2021.2014002"
    research_paper_details = get_research_paper_details_from_doi(doi)
    if research_paper_details:
        return JsonResponse({"research_paper_details": research_paper_details})
    else:
        return JsonResponse({"error": "Research paper not found."})        
    
    
    
