import csv
import sys
import time
from json.decoder import JSONDecodeError

import structlog

from deskflow.omnichat import list_chat_messages, list_chats

log = structlog.get_logger()


def list_all_chats_from_date(offset=0, limit=5, from_date="2021-05-01"):
    """Retrieve all chats given a start date.
    Args:
        offset (int) -- Quantos registros deve saltar para fazer a requisição.
        limit (int) -- Quantos registros retornar por requisição (Máximo 100).
        from_date (str) -- Uma data a partir da qual serão retornados os chats.
    """

    resp = list_chats(
        **{"createdAt.gt": from_date, "offset": offset, "limit": limit}
    )

    try:
        return resp
    except JSONDecodeError as e:
        log.exception(
            "Error parsing JSON response from Omnichat API", response=resp.text
        )
        raise e


def get_chat_omnichat_messages(chat_id, offset=0, limit=15):
    """Retrieve all messages given a chat id.

    Args:
        chat_id (str) -- Identificador do chat.
        offset (int) -- Quantos registros deve saltar para fazer a requisição.
        limit (int) -- Quantos registros retornar por requisição (Máximo 100).
    """

    resp = list_chat_messages(chat_id=chat_id, offset=offset, limit=limit)

    try:
        return resp
    except JSONDecodeError as e:
        log.exception(
            "Error parsing JSON response from Omnichat API", response=resp.text
        )
        raise e


def create_csv_writer(csv_file="file.csv", delimiter=";", quotechar='"'):
    return csv.writer(
        csv_file,
        quoting=csv.QUOTE_MINIMAL,
        delimiter=delimiter,
        quotechar=quotechar,
    )


def create_csv_header(csv_writer, header_row=[]):
    csv_writer.writerow(header_row)


""" Informar a data de inicio da busca, na execução do script. Ex: 2021-05-01"""
from_date = "{}".format(sys.argv[1:][0])
file_name = "chats_from_{}.csv".format(from_date)
file_path = f"{file_name}"


def start():
    with open(file_path, mode="w", newline="") as csv_file:
        csv_writer = create_csv_writer(csv_file=csv_file)

        # file header
        header_row = [
            "chat_id",
            "msisdn",
            "name",
            "text",
            "status",
            "created_at",
            "updated_at",
            "type",
            "attachment_url",
        ]
        create_csv_header(csv_writer, header_row)

        chat_offset = 0
        has_chats = True

        while has_chats:
            try:
                time.sleep(1)
                print(f"Current Chat Offset: {chat_offset}")
                chats = list_all_chats_from_date(
                    limit=5, offset=chat_offset, from_date=from_date
                )

                has_chats = len(chats) > 0

                for chat in chats:
                    message_offset = 0
                    chat_id = chat["objectId"]
                    has_messages = True

                    while has_messages:
                        time.sleep(1)
                        messages = get_chat_omnichat_messages(
                            chat_id=chat_id, offset=message_offset, limit=100
                        )
                        has_messages = len(messages) > 0

                        for message in messages:
                            name = chat["name"]
                            text = (
                                "text" in message
                                and message["text"].replace("\n", " ")
                                or "N/A"
                            )
                            attachment_url = (
                                "attachmentUrl" in message
                                and message["attachmentUrl"]
                                or ""
                            )
                            status = message["status"]
                            msisdn = chat["platformId"]
                            created_at = message["createdAt"]
                            updated_at = message["updatedAt"]
                            type = message["type"]

                            row_data = [
                                chat_id,
                                msisdn,
                                name,
                                text,
                                status,
                                created_at,
                                updated_at,
                                type,
                                attachment_url,
                            ]
                            csv_writer.writerow(row_data)

                        message_offset += len(messages)

                chat_offset += len(chats)
            except Exception as e:
                log.exception("Error retrieving chats", error=e)
                raise e


start()
