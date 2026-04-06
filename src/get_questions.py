"""
質問一覧取得 Lambda 関数
全ての質問と、各質問に対する回答数を返す
GSI（kind-index）を使用して kind="Q" の質問を query で取得する
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

# GSI のインデックス名
KIND_INDEX = "kind-index"


def lambda_handler(event, context):
    """質問一覧を取得し、各質問の回答数を含めて返す"""
    try:
        # GSI を使用して kind="Q" の質問を query で取得する
        response = table.query(
            IndexName=KIND_INDEX,
            KeyConditionExpression=Key("kind").eq("Q"),
        )
        questions = response.get("Items", [])

        # 各質問の回答数を取得する
        result = []
        for q in questions:
            question_id = q["question_id"]

            # 回答（kind が "A#" で始まるもの）の件数を取得する
            answer_response = table.query(
                KeyConditionExpression=Key("question_id").eq(question_id)
                & Key("kind").begins_with("A#"),
                Select="COUNT",
            )
            answer_count = answer_response.get("Count", 0)

            result.append(
                {
                    "question_id": question_id,
                    "question_text": q.get("question_text", ""),
                    "questioner_name": q.get("questioner_name", ""),
                    "question_datetime": q.get("question_datetime", ""),
                    "category": q.get("category", ""),
                    "answer_count": answer_count,
                }
            )

        # 質問日時の降順でソートする
        result.sort(key=lambda x: x["question_datetime"], reverse=True)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(result, ensure_ascii=False),
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
                {"message": "質問一覧の取得に失敗しました"}, ensure_ascii=False
            ),
        }
