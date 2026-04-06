"""
回答投稿 Lambda 関数
指定された質問に対する回答を DynamoDB に追加する
"""

import json
import os
from datetime import datetime, timezone, timedelta
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# 日本時間のタイムゾーン
JST = timezone(timedelta(hours=9))


def lambda_handler(event, context):
    """回答データを DynamoDB に追加する"""
    try:
        question_id = event["pathParameters"]["question_id"]
        body = json.loads(event.get("body", "{}"))

        answer_text = body.get("answer_text", "")
        answerer_name = body.get("answerer_name", "")

        # 入力バリデーション
        if not answer_text or not answerer_name:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"message": "回答内容と回答者名は必須です"}, ensure_ascii=False
                ),
            }

        # 質問の存在確認
        question_response = table.get_item(
            Key={"question_id": question_id, "kind": "Q"}
        )
        if "Item" not in question_response:
            return {
                "statusCode": 404,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": json.dumps(
                    {"message": "質問が見つかりません"}, ensure_ascii=False
                ),
            }

        # 既存の回答数を取得して次の連番を決定する
        answer_response = table.query(
            KeyConditionExpression=Key("question_id").eq(question_id)
            & Key("kind").begins_with("A#"),
            Select="COUNT",
        )
        next_number = answer_response.get("Count", 0) + 1
        kind = f"A#{next_number:04d}"

        # 回答日時を生成する（日本時間）
        now = datetime.now(JST)
        answer_datetime = now.strftime("%Y/%m/%d/%H:%M:%S")

        # DynamoDB に回答データを追加する
        table.put_item(
            Item={
                "question_id": question_id,
                "kind": kind,
                "answer_text": answer_text,
                "answerer_name": answerer_name,
                "answer_datetime": answer_datetime,
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
                    "message": "回答を投稿しました",
                    "kind": kind,
                    "answer_datetime": answer_datetime,
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
                {"message": "回答の投稿に失敗しました"}, ensure_ascii=False
            ),
        }
