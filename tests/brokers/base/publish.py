import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from propan.annotations import Logger
from propan.brokers._model import BrokerAsyncUsecase


class SimpleModel(BaseModel):
    r: str


now = datetime.now()


class BrokerPublishTestcase:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("message", "message_type", "expected_message"),
        (
            ("hello", str, None),
            (b"hello", bytes, None),
            (1, int, None),
            (1.0, float, None),
            (False, bool, None),
            ({"m": 1}, Dict[str, int], None),
            ([1, 2, 3], List[int], None),
            (SimpleModel(r="hello!"), SimpleModel, None),
            (SimpleModel(r="hello!"), dict, {"r": "hello!"}),
            (now, datetime, now),
        ),
    )
    async def test_serialize(
        self,
        full_broker: BrokerAsyncUsecase,
        mock: Mock,
        queue: str,
        message,
        message_type,
        expected_message,
    ):
        consume = asyncio.Event()
        mock.side_effect = lambda *_: consume.set()  # pragma: no branch

        @full_broker.handle(queue)
        async def handler(m: message_type, logger: Logger):
            mock(m)

        async with full_broker:
            await full_broker.start()

            await asyncio.wait(
                (
                    asyncio.create_task(full_broker.publish(message, queue)),
                    asyncio.create_task(consume.wait()),
                ),
                timeout=3,
            )

        if expected_message is None:
            expected_message = message

        mock.assert_called_with(expected_message)

    @pytest.mark.asyncio
    async def test_unwrap_dict(
        self, mock: Mock, queue: str, full_broker: BrokerAsyncUsecase
    ):
        consume = asyncio.Event()
        mock.side_effect = lambda *_: consume.set()

        @full_broker.handle(queue)
        async def m(a: int, b: int, logger: Logger):
            mock({"a": a, "b": b})

        async with full_broker:
            await full_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(full_broker.publish({"a": 1, "b": 1.0}, queue)),
                    asyncio.create_task(consume.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_with(
            {
                "a": 1,
                "b": 1,
            }
        )

    @pytest.mark.asyncio
    async def test_unwrap_list(
        self, mock: Mock, queue: str, full_broker: BrokerAsyncUsecase
    ):
        consume = asyncio.Event()
        mock.side_effect = lambda *_: consume.set()

        @full_broker.handle(queue)
        async def m(a: int, b: int, *args: Tuple[int, ...], logger: Logger):
            mock({"a": a, "b": b, "args": args})

        async with full_broker:
            await full_broker.start()
            await asyncio.wait(
                (
                    asyncio.create_task(full_broker.publish([1, 1.0, 2.0, 3.0], queue)),
                    asyncio.create_task(consume.wait()),
                ),
                timeout=3,
            )

        mock.assert_called_with(
            {
                "a": 1,
                "b": 1,
                "args": (2, 3)
            }
        )
