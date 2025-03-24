from google.cloud import firestore
from google.cloud.firestore_v1.collection import CollectionReference
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.base_query import FieldFilter, BaseQuery
from typing import Optional, Tuple
from google.cloud.firestore_v1.batch import WriteBatch

MAX_BATCH_SIZE = 400


class FirestoreMngr:
    def __init__(self, project_id, db_name):
        self.fs_instance = firestore.Client(project=project_id, database=db_name)
        self.batch_counter = 0
        self.current_batch = None

    def get_current_batch(self) -> WriteBatch:
        return self.fs_instance.batch()

    def get_collection(self, collection) -> CollectionReference:
        return self.fs_instance.collection(collection)

    def create_document_with_id(self, collection: str, document: dict, key: Optional[str] = None):
        doc_ref = self.fs_instance.collection(collection).document(key)
        doc_ref.set(document)

    def create_document_with_batch(self, batch: WriteBatch, collection: str, document: dict, key: Optional[str] = None):
        doc_ref = self.fs_instance.collection(collection).document(key)
        batch.set(doc_ref, document)

    def get_document_by_id(self, collection: str, document_id: str) -> dict:
        doc_ref = self.fs_instance.collection(collection).document(document_id)
        return doc_ref.get().to_dict()

    def get_document_reference_by_id(self, collection: str, document_id: str) -> DocumentReference:
        doc_ref = self.fs_instance.collection(collection).document(document_id)
        return doc_ref

    def __get_data_by_filters(self, collection: str, filters: [FieldFilter]) -> CollectionReference:
        collection = self.fs_instance.collection(collection)
        for f in filters:
            collection = collection.where(filter=f)
        return collection

    def get_data_by_filter(self, collection: str, filters: [FieldFilter]) -> CollectionReference:
        collection_ref = self.__get_data_by_filters(collection, filters)
        return collection_ref

    def get_data_by_order(self,
                          collection: str,
                          sort_by: str,
                          direction: str) -> BaseQuery:

        collection_ref = self.fs_instance.collection(collection)
        query = collection_ref.order_by(sort_by, direction=direction)
        return query

    def get_data_by_filter_and_order(self,
                                     collection: str,
                                     filters: [FieldFilter], sort_by: str,
                                     direction: str) -> BaseQuery:

        collection_ref = self.__get_data_by_filters(collection, filters)
        query = collection_ref.order_by(sort_by, direction=direction)
        return query

    def get_count_by_filters(self, collection: str, filters: [FieldFilter]) -> int:
        collection_ref = self.__get_data_by_filters(collection, filters)
        return collection_ref.count().get()[0][0].value

    def __persist_and_dequeue(self, current_batch: WriteBatch) -> Tuple[int, WriteBatch]:
        current_batch.commit()
        return 0, self.get_current_batch()

    def __persist_and_flush(self, current_batch: WriteBatch) -> WriteBatch:
        current_batch.commit()
        return self.get_current_batch()

    def flush_and_dequeue(self):
        if self.batch_counter > 0:
            self.current_batch.commit()
        self.batch_counter = 0

    def add_batch_documents(self,
                            collection: str,
                            document: dict,
                            key: Optional[str] = None) -> WriteBatch:
        if self.current_batch is None:
            self.current_batch = self.get_current_batch()

        if self.batch_counter < MAX_BATCH_SIZE:
            doc_ref = self.fs_instance.collection(collection).document(key)
            self.current_batch.set(doc_ref, document)
            self.batch_counter += 1
        else:
            self.current_batch = self.__persist_and_flush(self.current_batch)
            doc_ref = self.fs_instance.collection(collection).document(key)
            self.current_batch.set(doc_ref, document)
            self.batch_counter = 1

        return self.current_batch

    def persist_batch_documents(self, counter: int,
                                current_batch: WriteBatch,
                                force: Optional[bool] = False) -> Tuple[int, WriteBatch]:

        if counter < MAX_BATCH_SIZE:
            counter += 1

        if force or counter >= MAX_BATCH_SIZE:
            counter, current_batch = self.__persist_and_dequeue(current_batch)

        return counter, current_batch
