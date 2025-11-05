"""
Inspect hierarchy - Find unique document Structures -
 Helpful when you have multiple variations of document in a collection

 """

# learn.mongodb.com      -- Validation of the schema
# use validation to inspect schema for invalid documents - thru inverse validation 
# give me docs that dont adhere to my docs
# After that sequential update many operations to fix those invalid docs

# Atlas search - b uild index

# create text based search
# single collection pattern



class MongoStructure:

    def find_different_structures(self, collection, sample_size=5):
        """Find documents with different field structures"""
        pipeline = [
            {
                "$limit": 3000
            },
            {
                "$group": {
                    "_id": {
                        "fields": {
                            "$map": {
                                "input": {"$objectToArray": "$$ROOT"},
                                "as": "field",
                                "in": "$$field.k"
                            }
                        }
                    },
                    "count": {"$sum": 1},
                    "samples": {"$push": {"_id": "$_id", "doc": "$$ROOT"}}
                }
            },
            {
                "$project": {
                    "fields": "$_id.fields",
                    "count": 1,
                    "sample_docs": {"$slice": ["$samples", sample_size]},
                    "_id": 0
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        return list(collection.aggregate(pipeline, allowDiskUse=True))

    def get_structure(self,collection):
        structures = self.find_different_structures(collection=collection)
        for i, struct in enumerate(structures):
            print(f"\nStructure {i+1}: {struct['count']} documents")
            print(f"Fields: {sorted(struct['fields'])}")
            print("Sample _id:", struct['sample_docs'][0]['_id'])
