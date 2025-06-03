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
from django.utils import timezone
import uuid

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


@api_view(["POST"])
def send_message(request):
    """
    Temporary endpoint to handle chat messages
    """
    try:
        message = request.data.get('message')
        conversation_id = request.data.get('conversation_id')
        
        # For now, just echo back a response
        response = {
            'message': f"Echo: {message}",
            'conversation_id': conversation_id,
            'timestamp': str(timezone.now())
        }
        
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def create_conversation(request):
    """
    Create a new conversation
    """
    try:
        name = request.data.get('name', 'New Conversation')
        user_id = request.data.get('user_id')
        
        # For now, just return a mock conversation object
        conversation = {
            'id': str(uuid.uuid4()),
            'name': name,
            'user_id': user_id,
            'created_at': str(timezone.now()),
            'messages': []
        }
        
        return JsonResponse(conversation)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def get_conversations(request):
    """
    Get all conversations for a user
    """
    try:
        user_id = request.GET.get('user_id')
        
        # For now, return mock conversations
        conversations = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Sample Conversation 1',
                'user_id': user_id,
                'created_at': str(timezone.now()),
                'messages': []
            }
        ]
        
        return JsonResponse({'conversations': conversations})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["DELETE"])
def delete_conversation(request, conversation_id):
    """
    Delete a conversation
    """
    try:
        # For now, just return success
        return JsonResponse({'success': True, 'message': f'Conversation {conversation_id} deleted'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



