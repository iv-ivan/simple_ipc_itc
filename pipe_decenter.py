from multiprocessing import Process, Pipe
import time
import select

_EVENT_MASK = (select.POLLIN | select.POLLPRI | select.POLLERR |
               select.POLLHUP | select.POLLNVAL)

def logger(main_to_log_r, time_to_log_r):
    poll_obj = select.poll()
    poll_obj.register(main_to_log_r.fileno(), _EVENT_MASK)
    poll_obj.register(time_to_log_r.fileno(), _EVENT_MASK)
    cur_t = None
    while True:
        for (fd, event) in poll_obj.poll():
            if fd == time_to_log_r.fileno():
                print("TS_logger {}".format(event))
                cur_t = time_to_log_r.recv()
                continue
            if fd == main_to_log_r.fileno():
                print("MAIN {}".format(event))
                log_rec = main_to_log_r.recv()
                print("{}: {}".format(cur_t, log_rec))
                continue


def timer(time_to_main_w, time_to_log_w):
    while True:
        cur_t = str(int(time.time()))
        time_to_main_w.send(cur_t)
        time_to_log_w.send(cur_t)
        time.sleep(1)


def reader(input_to_main_w):
    i = 0
    while True:
        input_to_main_w.send(str(i))
        i += 1
        time.sleep(1)


if __name__ == '__main__': 
    main_to_log_w, main_to_log_r = Pipe()
    time_to_log_w, time_to_log_r = Pipe()
    log_proc = Process(target=logger, args=(main_to_log_r, time_to_log_r))
    log_proc.start()
    main_to_log_r.close()
    time_to_log_r.close()

    time_to_main_w, time_to_main_r = Pipe()
    time_proc = Process(target=timer, args=(time_to_main_w, time_to_log_w))
    time_proc.start()
    time_to_main_w.close()
    time_to_log_w.close()

    input_to_main_w, input_to_main_r = Pipe()
    input_proc = Process(target=reader, args=(input_to_main_w,))
    input_proc.start()
    input_to_main_w.close()

    try:
        poll_obj = select.poll()
        poll_obj.register(input_to_main_r.fileno(), _EVENT_MASK)
        poll_obj.register(time_to_main_r.fileno(), _EVENT_MASK)
        cur_t = None
        while True:
            for (fd, event) in poll_obj.poll(1000):
                if fd == time_to_main_r.fileno():
                    print("TS {}".format(event))
                    cur_t = time_to_main_r.recv()
                    continue
                if fd == input_to_main_r.fileno():
                    print("LOG {}".format(event))
                    text = input_to_main_r.recv()
                    main_to_log_w.send('{} ({})'.format(text, cur_t))
                    print('{} ({})'.format(text, cur_t))
                    continue

    except Exception as e:
        print(type(e))
    finally:
        log_proc.terminate()
        time_proc.terminate()
        input_proc.terminate()