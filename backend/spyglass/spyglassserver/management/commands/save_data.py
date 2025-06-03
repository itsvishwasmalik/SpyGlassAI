from django.core.management.base import BaseCommand
from spyglassserver.models import ResearchPaper
import json
import os
from django.conf import settings
from django.utils import timezone
from django.db import models

def save_scopus_data(year=2023):
    """
    Save Scopus data from JSON files to the database.
    
    Args:
        year (int): The year of the data to be saved. Default is 2023.
    Returns:
        int: Number of papers successfully saved
    """
    # Define the path to the JSON files
    json_path = os.path.join(settings.BASE_DIR, 'spyglassserver', 'scopus', 'output', str(year))
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Directory not found: {json_path}")
    
    # Get all JSON files in the directory
    json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {json_path}")
    
    papers_saved = 0
    for json_file in json_files:
        file_path = os.path.join(json_path, json_file)
        
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Check if paper already exists
        if ResearchPaper.objects.filter(eid=data.get('eid')).exists():
            print(f"Paper with EID {data.get('eid')} already exists, skipping...")
            continue
        
        try:
            # Create a ResearchPaper object and save it to the database
            research_paper = ResearchPaper(
                eid = data.get('eid'),
                doi = data.get('doi'),
                pii = data.get('pii'),
                pubmed_id = data.get('pubmed_id'),
                title = data.get('title'),
                subtype = data.get('subtype'),
                subtypeDescription = data.get('subtypeDescription'),
                creator = data.get('creator'),
                afid = data.get('afid'),
                affilname = data.get('affilname'),
                affiliation_city = data.get('affiliation_city'),
                affiliation_country = data.get('affiliation_country'),
                author_count = data.get('author_count'),
                author_names = data.get('author_names'),
                author_ids = data.get('author_ids'),
                author_afids = data.get('author_afids'),
                coverDate = data.get('coverDate'),
                coverDisplayDate = data.get('coverDisplayDate'),
                publicationName = data.get('publicationName'),
                issn = data.get('issn'),
                source_id = data.get('source_id'),
                eIssn = data.get('eIssn'),
                aggregationType = data.get('aggregationType'),
                volume = data.get('volume'),
                issueIdentifier = data.get('issueIdentifier'),
                article_number = data.get('article_number'),
                pageRange = data.get('pageRange'),
                description = data.get('description'),
                authkeywords = data.get('authkeywords'),
                citedby_count = data.get('citedby_count'),
                openaccess = data.get('openaccess'),
                freetoread = data.get('freetoread'),
                freetoreadLabel = data.get('freetoreadLabel'),
                fund_acr = data.get('fund_acr'),
                fund_no = data.get('fund_no'),
                fund_sponsor = data.get('fund_sponsor'),
                ref_docs = json.dumps(data.get('ref_docs', [])),  # Convert list to JSON string
                created_at = timezone.now(),
                updated_at = timezone.now(),
            )
            
            # Save the object to the database
            research_paper.save()
            papers_saved += 1
            print(f"Saved data for EID: {research_paper.eid}")
            
        except Exception as e:
            print(f"Error saving paper from {json_file}: {str(e)}")
            continue
    
    return papers_saved

class Command(BaseCommand):
    help = 'Imports research paper data into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=2023,
            help='Year of the Scopus data to import (default: 2023)'
        )

    def handle(self, *args, **options):
        year = options['year']
        
        try:
            self.stdout.write(f'Starting to save Scopus data for the year {year}...')
            papers_saved = save_scopus_data(year)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully saved {papers_saved} papers from {year}.')
            )
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {str(e)}')
            )

