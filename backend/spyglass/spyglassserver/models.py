from django.db import models
from django.contrib.auth.models import User

class SpyglassUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default='USER')  # USER, ADMIN
    token = models.CharField(max_length=36, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'spyglass_user'

    def __str__(self):
        return f"{self.user.email} - {self.role}"
class ResearchPaper(models.Model):
    eid = models.CharField(max_length=255, unique=True)
    doi = models.CharField(max_length=255, null=True, blank=True)
    pii = models.CharField(max_length=255, null=True, blank=True)
    pubmed_id = models.CharField(max_length=255, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    subtype = models.CharField(max_length=50, null=True, blank=True)
    subtypeDescription = models.CharField(max_length=50, null=True, blank=True)
    creator = models.CharField(max_length=255, null=True, blank=True)
    afid = models.CharField(max_length=255, null=True, blank=True)
    affilname = models.CharField(max_length=255, null=True, blank=True)
    affiliation_city = models.CharField(max_length=255, null=True, blank=True)
    affiliation_country = models.CharField(max_length=255, null=True, blank=True)
    author_count = models.IntegerField(null=True, blank=True)
    author_names = models.TextField(null=True, blank=True)
    author_ids = models.TextField(null=True, blank=True)
    author_afids = models.TextField(null=True, blank=True)
    coverDate = models.DateField(null=True, blank=True)
    coverDisplayDate = models.CharField(max_length=50, null=True, blank=True)
    publicationName = models.CharField(max_length=255, null=True, blank=True)
    issn = models.CharField(max_length=20, null=True, blank=True)
    source_id = models.CharField(max_length=20, null=True, blank=True)
    eIssn = models.CharField(max_length=20, null=True, blank=True)
    aggregationType = models.CharField(max_length=50, null=True, blank=True)
    volume = models.CharField(max_length=20, null=True, blank=True)
    issueIdentifier = models.CharField(max_length=20, null=True, blank=True)
    article_number = models.CharField(max_length=50, null=True, blank=True)
    pageRange = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    authkeywords = models.TextField(null=True, blank=True)
    citedby_count = models.IntegerField(null=True, blank=True)
    openaccess = models.BooleanField(default=False)
    freetoread = models.CharField(max_length=50, null=True, blank=True)
    freetoreadLabel = models.CharField(max_length=50, null=True, blank=True)
    fund_acr = models.TextField(null=True, blank=True)
    fund_no = models.TextField(null=True, blank=True)
    fund_sponsor = models.TextField(null=True, blank=True)
    ref_docs = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    