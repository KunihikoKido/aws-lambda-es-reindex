# Elasticsearch Reindex for AWS Lambda

## About

#### Runtime
Python 2.7

#### Lambda Hander
lambda_function.lambda_handler

#### Input event

Example: Input event:
```json
{
  "source_host": "http://<your_elasticsearch_server:9200>/",
  "source_index": "blog",
  "target_host": "http://<your_elasticsearch_server:9200>/",
  "target_index": "blog",
  "scroll": "5m",
  "scan_options": {
    "size": 100
  },
  "bulk_options": {
    "chunk_size": 100
  }
}
```

* ``source_host``: index to read documents from.
* ``source_index``: index to read documents from.
* ``target_host``: (Optional) is specified will be used for writing. default to ``source_host``
* ``target_index``: (Optional) name of the index in the target cluster to populate. default to ``source_index``
* ``scroll``: (Optional) keep the scroll open for another minute. default to ``5m``
* ``scan_options.size``: (Optional) you will get back a maximum of size * number_of_primary_shards documents in each batch. default to ``500``
* ``bulk_options.chunk_size``: (Optional) number of docs in one chunk sent to es. default to ``500``


Example: Minimum:
```json
{
  "source_host": "http://<your_elasticsearch_server:9200>/",
  "source_index": "blog"
}
```

Example: Transfer data to a another:
```json
{
  "source_host": "http://<your_elasticsearch_server:9200>/",
  "source_index": "blog1",
  "target_host": "http://<your_elasticsearch_server:9200>/",
  "target_index": "blog2",
}
```

#### Execution result

Execution result sample:
```json
null
```
