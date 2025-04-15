from pymongo import MongoClient
from django.conf import settings

class MongoDB:
    def __init__(self, uri, database_name, collection_name):
        self.client = MongoClient(uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def create_document(self, data, id):
        """
        Inserts a document into the collection.
        :param data: dict containing the document data
        :return: ID of the inserted document
        """
        try:
            if '_id' not in data:
                data['_id'] = str(id) 
            # Insert the document
            result = self.collection.insert_one(data)
            return str(data['_id'])

        except Exception as e:
            print("An error occurred while inserting document: ", e)
            return None

    def read_document(self, document_id):
        """
        Retrieves a document from the collection by its ID.
        :param document_id: str ID of the document to retrieve
        :return: dict containing the document data or None if not found
        """
        try:
            document = self.collection.find_one({"_id": str(document_id)})
            # remove the _id field from the document
            if document:
                document.pop('_id', None)
            return document
        except Exception as e:
            print("An error occurred while reading document: ", e)
            return None
    
    def read_document_by_query(self, query):
        """
        Retrieves a document from the collection by its ID.
        :param document_id: str ID of the document to retrieve
        :return: dict containing the document data or None if not found

        Example :
        ids = ['id1', 'id2', 'id3']
        query = {"_id": {"$in": ids}}
        documents = mongo_db.read_documents_by_query(query)
        """
        try:
            document = self.collection.find_one(query)
            return document
        except Exception as e:
            print("An error occurred while reading document: ", e)
            return None

    def read_all_documents(self):
        """
        Retrieves all documents from the collection.
        :return: list of dicts containing the document data
        """
        try:
            documents = self.collection.find()
            return list(documents)
        except Exception as e:
            print("An error occurred while reading all documents: ", e)
            return None

    def update_document(self, document_id, update_data):
        """
        Updates a document in the collection by its ID.
        :param document_id: str ID of the document to update
        :param update_data: dict containing the updated data
        :return: result of the update operation
        """
        try:
            result = self.collection.update_one({"_id": document_id}, {"$set": update_data})
            return result.modified_count
        except Exception as e:
            print("An error occurred while updating document: ", e)
            return None

    def delete_document(self, document_id):
        """
        Deletes a document from the collection by its ID.
        :param document_id: str ID of the document to delete
        :return: result of the delete operation
        """
        try:
            print("document_id to be deleted",document_id)
            result = self.collection.delete_one({"_id": str(document_id)})
            return result.deleted_count
        except Exception as e:
            print("An error occurred while deleting document: ", e)
            return None
        
    def delete_document_by_query(self, query):
        """
        Deletes a document from the collection by its ID.
        :param document_id: str ID of the document to delete
        :return: result of the delete operation
        """
        try:
            result = self.collection.delete_one(query)
            return result.deleted_count
        except Exception as e:
            print("An error occurred while deleting document: ", e)
            return None
        
    def delete_all_documents(self):
        """
        Deletes all documents from the collection.
        :return: result of the delete operation
        """
        try:
            result = self.collection.delete_many({})
            return result.deleted_count
        except Exception as e:
            print("An error occurred while deleting all documents: ", e)
            return None