from asyncio import AbstractEventLoop
from concurrent.futures.thread import ThreadPoolExecutor
from typing import IO, Any, AnyStr, AsyncIterable, Callable, Union

import asyncfiles

from blacksheep.utils.aio import get_running_loop


class PoolClient:
    def __init__(
        self,
        loop: AbstractEventLoop | None = None,
        executor: ThreadPoolExecutor | None = None,
    ):
        self._loop = loop or get_running_loop()
        self._executor = executor

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    async def run(self, func, *args) -> Any:
        return await self._loop.run_in_executor(self._executor, func, *args)


class FileContext(PoolClient):
    def __init__(
        self,
        file_path: str,
        *,
        loop: AbstractEventLoop | None = None,
        mode: str = "rb",
    ):
        super().__init__(loop)
        self._file_path = file_path
        self._file = None
        self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def file(self) -> Any:
        if self._file is None:
            raise TypeError("The file is not open.")
        return self._file

    async def seek(self, offset: int, whence: int = 0) -> None:
        self.file.seek(offset, whence)

    async def read(self, chunk_size: int | None = None) -> bytes:
        return await self.file.read(-1 if chunk_size is None else chunk_size)

    async def write(
        self, data: Union[AnyStr, Callable[[], AsyncIterable[AnyStr]]]
    ) -> None:
        f = self.file
        if isinstance(data, (bytes, str)):
            await f.write(data)
        else:
            async for chunk in data():
                await f.write(chunk)

    async def chunks(self, chunk_size: int = 1024 * 64) -> AsyncIterable[AnyStr]:
        f = self.file
        while True:
            chunk = await f.read(chunk_size)

            if not chunk:
                break

            yield chunk
        yield b""

    async def open(self) -> Any:
        try:
            f = asyncfiles.open(str(self._file_path), self._mode, loop=self._loop)
        except ValueError as exc:
            raise ValueError(f"invalid mode: {self._mode!r}") from exc
        return await f.__aenter__()

    async def __aenter__(self):
        self._file = await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if self._file is not None:
                await self._file.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self._file = None


class FilesHandler:
    """Provides methods to handle files asynchronously."""

    def open(
        self, file_path: str, mode: str = "rb", loop: AbstractEventLoop | None = None
    ) -> FileContext:
        return FileContext(file_path, mode=mode, loop=loop)

    async def read(
        self, file_path: str, size: int | None = None, mode: str = "rb"
    ) -> AnyStr:
        async with self.open(file_path, mode=mode) as file:
            return await file.read(size)

    async def write(
        self,
        file_path: str,
        data: Union[AnyStr, Callable[[], AsyncIterable[AnyStr]]],
        mode: str = "wb",
    ) -> None:
        async with self.open(file_path, mode=mode) as file:
            await file.write(data)

    async def chunks(
        self, file_path: str, chunk_size: int = 1024 * 64
    ) -> AsyncIterable[AnyStr]:
        async with self.open(file_path) as file:
            async for chunk in file.chunks(chunk_size):
                yield chunk
