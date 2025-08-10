# run_ingestion.py
from datahub.ingestion.run.pipeline import Pipeline

pipeline = Pipeline.create({
    "source": {
        "type": "custom-python",
        "config": {
            "module_name": "custom_csw_extractor",
            "class_name": "CSWExtractor",
            "csw_endpoint": "https://www.idee.es/csw-inspire-idee/srv/spa/csw",
            "filter_keywords": ["agua", "zonas"],
            "limit": 10,
            "platform_urn": "urn:li:dataPlatform:CustomService",
            "environment": "PROD"
        }
    },
    "sink": {
        "type": "file",
        "config": {
            "filename": "./csw_output.json"
        }
    }
})

pipeline.run()
pipeline.raise_from_status()
