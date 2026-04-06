"""
質問投稿 Lambda 関数
新しい質問を DynamoDB に追加する
"""

import json
import os
import uuid
from datetime import datetime, timezone, timedelta
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=9))


def lambda_handler(event, context):
    """質問データを DynamoDB に追加する"""
    try:
        body = json.loads(event.get("body", "{}"))

        question_text = body.get("question_text", "")
        questioner_name = body.get("questioner_name", "")
        category = body.get("category", "")

        # 入力バリデーション
        if not question_text or not questioner_name:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"message": "質問内容と質問者名は必須です"}, ensure_ascii=False
                ),
            }

        # ユニークな質問IDを生成する
        question_id = str(uuid.uuid4())

        # 質問日時を生成する（日本時間）
        now = datetime.now(JST)
        question_datetime = now.strftime("%Y/%m/%d/%H:%M:%S")

        # DynamoDB に質問データを追加する
        table.put_item(
            Item={
                "question_id": question_id,
                "kind": "Q",
                "question_text": question_text,
                "questioner_name": questioner_name,
                "question_datetime": question_datetime,
                "category": category,
            }
        )

        return {
            "statusCode": 201,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "message": "質問を投稿しました",
                    "question_id": question_id,
                    "question_datetime": question_datetime,
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"message": "質問の投稿に失敗しました"}, ensure_ascii=False
            ),
        }
