import asyncio
from unittest.mock import Mock

import anyio
import pytest

from propan.broker.core.abc import BrokerUsecase


class BrokerRPCTestcase:
    @pytest.mark.asyncio
    async def test_rpc(self, queue: str, full_broker: BrokerUsecase):
        @full_broker.subscriber(queue)
        async def m():  # pragma: no cover
            return "1"

        await full_broker.start()

        r = await full_broker.publish("hello", queue, rpc_timeout=3, rpc=True)
        assert r == "1"

    @pytest.mark.asyncio
    async def test_rpc_timeout_raises(self, queue: str, full_broker: BrokerUsecase):
        @full_broker.subscriber(queue)
        async def m():  # pragma: no cover
            await anyio.sleep(1)

        await full_broker.start()

        with pytest.raises(TimeoutError):  # pragma: no branch
            await full_broker.publish(
                "hello",
                queue,
                rpc=True,
                rpc_timeout=0,
                raise_timeout=True,
            )

    @pytest.mark.asyncio
    async def test_rpc_timeout_none(self, queue: str, full_broker: BrokerUsecase):
        @full_broker.subscriber(queue)
        async def m():  # pragma: no cover
            await anyio.sleep(1)

        await full_broker.start()

        r = await full_broker.publish(
            "hello",
            queue,
            rpc=True,
            rpc_timeout=0,
        )

        assert r is None

    @pytest.mark.asyncio
    async def test_rpc_with_reply(
        self, queue: str, mock: Mock, full_broker: BrokerUsecase
    ):
        consume = asyncio.Event()
        mock.side_effect = lambda *_: consume.set()  # pragma: no branch
        reply_queue = queue + "1"

        @full_broker.subscriber(reply_queue)
        async def response_hanler(m: str):
            mock(m)

        @full_broker.subscriber(queue)
        async def m():  # pragma: no cover
            return "1"

        await full_broker.start()

        await full_broker.publish("hello", queue, reply_to=reply_queue)
        await asyncio.wait_for(consume.wait(), 3)

        mock.assert_called_with("1")


class ReplyAndConsumeForbidden:
    @pytest.mark.asyncio
    async def test_rpc_with_reply_and_callback(self, full_broker: BrokerUsecase):
        with pytest.raises(ValueError):
            await full_broker.publish(
                "hello",
                "some",
                reply_to="some",
                rpc=True,
                rpc_timeout=0,
            )
