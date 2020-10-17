from multiprocessing import Process
import time
import select
import socket

_EVENT_MASK = (select.POLLIN | select.POLLPRI | select.POLLERR |
               select.POLLHUP | select.POLLNVAL)

_PORT = 9090
_LOGGER_PORT = 9091

_SIZE = 1024

def logger():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', _LOGGER_PORT))
    sock.listen(1)
    conn1, addr1 = sock.accept()
    conn2, addr2 = sock.accept()
    print('connected1_logger:', addr1)
    print('connected2_logger:', addr2)

    socket_time = conn1
    socket_main = conn2
    poll_obj = select.poll()
    poll_obj.register(socket_main.fileno(), _EVENT_MASK)
    poll_obj.register(socket_time.fileno(), _EVENT_MASK)
    cur_t = None
    while True:
        for (fd, event) in poll_obj.poll():
            if fd == socket_time.fileno():
                if event == 19:
                    raise Exception('bad pipe')
                print("TS_logger {}".format(event))
                cur_t = socket_time.recv(_SIZE).decode()
                continue
            if fd == socket_main.fileno():
                if event == 19:
                    raise Exception('bad pipe')
                print("MAIN {}".format(event))
                log_rec = socket_main.recv(_SIZE).decode()
                print("{}: {}".format(cur_t, log_rec))
                continue


def timer():
    sock_main = socket.socket()
    sock_main.connect(('localhost', _PORT))

    sock_log = socket.socket()
    sock_log.connect(('localhost', _LOGGER_PORT))
    while True:
        cur_t = str(int(time.time()))
        sock_main.send(cur_t.encode())
        sock_log.send(cur_t.encode())
        time.sleep(1)


def reader():
    time.sleep(1)
    sock_main = socket.socket()
    sock_main.connect(('localhost', _PORT))

    i = 0
    while True:
        sock_main.send(str(i).encode())
        i += 1
        time.sleep(1)


if __name__ == '__main__': 
    log_proc = Process(target=logger, args=())
    log_proc.start()
    
    time_proc = Process(target=timer, args=())
    time_proc.start()
   
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', _PORT))
    sock.listen(1)

    input_proc = Process(target=reader, args=())
    input_proc.start()

    conn1, addr1 = sock.accept()
    conn2, addr2 = sock.accept()
    print('connected1:', addr1)
    print('connected2:', addr2)

    time.sleep(1)
    sock_log = socket.socket()
    sock_log.connect(('localhost', _LOGGER_PORT))

    conn_input = conn1
    conn_time = conn2
    try:
        poll_obj = select.poll()
        poll_obj.register(conn_time.fileno(), _EVENT_MASK)
        poll_obj.register(conn_input.fileno(), _EVENT_MASK)
        cur_t = None
        while True:
            for (fd, event) in poll_obj.poll(1000):
                if fd == conn_time.fileno():
                    if event == 19:
                        raise Exception('bad pipe')
                    print("TS {}".format(event))
                    cur_t = conn_time.recv(_SIZE).decode()
                    continue
                if fd == conn_input.fileno():
                    if event == 19:
                        raise Exception('bad pipe')
                    print("LOG {}".format(event))
                    text = conn_input.recv(_SIZE).decode()
                    sock_log.send('{} ({})'.format(text, cur_t).encode())
                    #print('{} ({})'.format(text, cur_t))
                    continue

    except Exception as e:
        print(type(e), e)
    finally:
        log_proc.terminate()
        time_proc.terminate()
        input_proc.terminate()