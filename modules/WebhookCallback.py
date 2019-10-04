from modules.DatabaseObject import DatabaseObject
import hashlib
import random


class WebhookCallback(DatabaseObject):

    local_exclusions = [
        'PROCESSING_STATE_QUEUED',
        'PROCESSING_STATE_PROCESSING',
        'PROCESSING_STATE_COMPLETE',
        'PROCESSING_STATE_ERROR'
    ]

    PROCESSING_STATE_QUEUED = 0,
    PROCESSING_STATE_PROCESSING = 1
    PROCESSING_STATE_COMPLETE = 2
    PROCESSING_STATE_ERROR = 100

    id = None
    slug = None
    function = None
    parameters = None
    processing_state = None
    webhook_url = None
    error_message = None
    ctime = None
    mtime = None

    def generate_slug(self, slug_length=16):
        random.seed()
        alpha = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        slug = ""
        for i in range(0, slug_length):
            slug += random.choice(alpha)
        return slug

    @staticmethod
    def fetch_by_function(
        database_manager,
        function
    ):
        conditions = [
            {
                "column": "function",
                "equivalence": "=",
                "value": function
            },
            {
                "column": "processing_state",
                "equivalence": "=",
                "value": WebhookCallback.PROCESSING_STATE_QUEUED
            }
        ]
        return WebhookCallback.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = WebhookCallback(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj
