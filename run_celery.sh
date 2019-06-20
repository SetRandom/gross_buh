#!/bin/sh
celery -A celery_worker worker -B -l info