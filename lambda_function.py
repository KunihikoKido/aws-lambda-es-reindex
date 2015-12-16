# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import json
import boto3
import logging
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch.exceptions import ElasticsearchException

import settings

logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

RESULT_SUCCESS = {"acknowledged": True}

class ScrollError(ElasticsearchException):
    pass

def lambda_handler(event, context):
    def _is_valid(event):
        if event.get('source_host') and event.get('source_index'):
            return True
        return False

    if not _is_valid(event):
        message = 'Invalid Parameters: {}'.format(event)
        logger.error(message)
        return {'error': message}

    source_host = event.get('source_host')
    source_index = event.get('source_index')
    source_client = elasticsearch_client(source_host)

    target_host = event.get('target_host', source_host)
    target_index = event.get('target_index', source_index)
    target_client = elasticsearch_client(target_host)

    scroll_id = event.get('scroll_id', None)
    scroll = event.get('scroll', settings.DEFAULT_SCROLL)

    scan_options = event.get('scan_options', settings.DEFAULT_SCAN_OPTIONS)
    bulk_options = event.get('bulk_options', settings.DEFAULT_BULK_OPTIONS)

    if scroll_id is None:
        try:
            scroll_id = scan_search(
                source_client, index=source_index, scroll=scroll, **scan_options)
        except Exception as e:
            logger.error(e)
            return {'error': str(e)}

        if scroll_id:
            event['scroll_id'] = scroll_id
            invoke_reindex(event, context)
            return RESULT_SUCCESS
        else:
            message = 'Can not get the scroll_id: {source_host} {source_index}'.format(**event)
            logger.error(message)
            return {'error': message}

    docs, scroll_id = scroll_search(source_client, scroll_id, scroll=scroll)

    if scroll_id is None or not docs:
        logger.info('Finished: {}'.format(event))
        return RESULT_SUCCESS

    success, errors = bulk_index(
        target_client, docs, target_index, **bulk_options)
    logger.info({"success": success, "errors": errors})


    event['scroll_id'] = scroll_id
    invoke_reindex(event, context)

    return RESULT_SUCCESS

def elasticsearch_client(host):
    return Elasticsearch(host, timeout=settings.TIMEOUT, send_get_body_as='POST')

def scan_search(client, index, scroll='1m', size=10, **kwargs):
    kwargs['search_type'] = 'scan'
    kwargs['fields'] = ('_source', '_parent', '_routing', '_timestamp')
    response = client.search(index=index, scroll=scroll, size=size, **kwargs)
    return response.get('_scroll_id', None)


def scroll_search(client, scroll_id, scroll='1m', **kwargs):
    response = client.scroll(scroll_id, scroll=scroll, **kwargs)

    if response['_shards']['failed']:
        raise ScrollError(
            'Scroll request has failed on {} shards out of {}.'.format(
                response['_shards']['failed'], response['_shards']['total']
            )
        )

    docs = response['hits']['hits']
    scroll_id = response.get('_scroll_id', None)
    return docs, scroll_id


def invoke_reindex(event, context):
    if settings.DEBUG:
        return lambda_handler(event, context)

    client = boto3.client('lambda')
    client.invoke(
        FunctionName=context.function_name,
        InvocationType='Event',
        LogType='None',
        Payload=json.dumps(event)
    )


def bulk_index(client, docs, index, chunk_size=500, **kwargs):
    def _change_doc_index(docs, index):
        for d in docs:
            d['_index'] = index
            if 'fields' in d:
                d.update(d.pop('fields'))
            yield d

    kwargs['stats_only'] = True
    return helpers.bulk(client,
        _change_doc_index(docs, index), chunk_size=chunk_size, **kwargs)
