import logging
import selectors

import message_util

from proto_reader import ProtoReader
from proto_writer import ProtoWriter


class ConnectedClient:
    """Server representation of a connected client."""

    def __init__(self, connection_socket, client_address, selector):
        self.socket = connection_socket
        self.address = client_address
        self.selector = selector
        self.reader = ProtoReader(self.socket)
        self.writer = ProtoWriter(self.socket)
        self.__reset()
        self.__processed_count = 0

    def __reset(self):
        self.request = None
        self.response_created = False
        self.reader.reset()

    def activate(self):
        """Activates the connection to the client to start receiving data."""
        self.selector.register(self.socket, selectors.EVENT_READ, data=self)

    def __set_read_mode(self):
        """Sets selector to look for read events."""
        self.selector.modify(self.socket, selectors.EVENT_READ, data=self)

    def __set_write_mode(self):
        """Sets selector to look for write events."""
        self.selector.modify(self.socket, selectors.EVENT_WRITE, data=self)

    def process_events(self, mask):
        """Processes events."""
        if mask & selectors.EVENT_READ:
            message = self.reader.read()
            if message and not self.request:
                self.__process_request(**message)

        if mask & selectors.EVENT_WRITE:
            if self.request:
                if not self.response_created:
                    message = self.__create_response()
                    self.writer.set_buffer(message)
                if self.writer.write():
                    logging.debug(f"Sent response to {self.address[0]}:{self.address[1]}")
                    self.__reset()
                    self.__set_read_mode()

    def close(self):
        """Closes the connection to the client."""
        logging.debug(f"Closing connection to {self.address[0]}:{self.address[1]}")
        try:
            self.selector.unregister(self.socket)
        except Exception as e:
            logging.error(f"selector.unregister() exception for {self.address}: {repr(e)}")

        try:
            self.socket.close()
        except OSError as e:
            logging.error(f"socket.close() exception for {self.address}: {repr(e)}")
        finally:
            self.socket = None

    def __process_request(self, header, payload):
        if header["content-type"] == "text/json":
            encoding = header["content-encoding"]
            self.request = message_util.json_decode(payload, encoding)
            logging.debug(f"Received request {repr(self.request)} from {self.address[0]}:{self.address[1]}")
        else:
            # Binary or unknown content-type
            self.request = payload
            logging.debug(f"Received {header['content-type']} request from {self.address}")

        # Set selector to listen for write events, we're done reading.
        self.__set_write_mode()
        self.__processed_count += 1

    def __create_response(self):
        action = self.request.get("action")
        value = self.request.get("value")
        response = message_util.create_response_json_content(action, value)
        message = message_util.create_message(**response)
        self.response_created = True
        return message
