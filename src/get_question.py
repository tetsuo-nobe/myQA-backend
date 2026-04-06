"""
質問詳細＋回答一覧取得 Lambda 関数
指定された質問IDの質問詳細と、その質問に対する全回答を返す
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def lambda_handler(event, context):
    """質問詳細と回答一覧を取得する"""
    try:
        question_id = event["pathParameters"]["question_id"]

        # 指定された question_id の全アイテム（質問＋回答）を取得する
        response = table.query(
            KeyConditionExpression=Key("question_id").eq(question_id)
        )
        items = response.get("Items", [])

        if not items:
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

        # 質問データと回答データを分離する
        question = None
        answers = []
        for item in items:
            if item["kind"] == "Q":
                question = {
                    "question_id": item["question_id"],
                    "question_text": item.get("question_text", ""),
                    "questioner_name": item.get("questioner_name", ""),
                    "question_datetime": item.get("question_datetime", ""),
                    "category": item.get("category", ""),
                }
            elif item["kind"].startswith("A#"):
                answers.append(
                    {
                        "kind": item["kind"],
                        "answer_text": item.get("answer_text", ""),
                        "answerer_name": item.get("answerer_name", ""),
                        "answer_datetime": item.get("answer_datetime", ""),
                    }
                )

        # 回答を kind（連番）の昇順でソートする
        answers.sort(key=lambda x: x["kind"])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {"question": question, "answers": answers}, ensure_ascii=False
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
                {"message": "質問詳細の取得に失敗しました"}, ensure_ascii=False
            ),
        }
