#include <iostream>
#include <thread>
#include <condition_variable>
#include <mutex>
#include <queue>

using namespace std;

struct Stream {
    queue<string> q;
    mutex mt;
    condition_variable cv;
};

void logger(shared_ptr<Stream> log_q) {
    string cur_t;
    while(true) {
        std::unique_lock<std::mutex> lk(log_q->mt);
        log_q->cv.wait(lk, [&log_q]{return !log_q->q.empty();});
        string message = log_q->q.front();
        log_q->q.pop();
        lk.unlock();
        
        if (message.find("TS") != std::string::npos) {
            cur_t = message.substr(3);
        } else {
            cout << cur_t << ": " << message << endl;
        }
    }
}

void timer(shared_ptr<Stream> log_q, shared_ptr<Stream> main_q) {
    size_t time = 123456;
    while (true) {
        {
            lock_guard<mutex> lk(main_q->mt);
            main_q->q.push("TS " + to_string(time));
        }
        {
            lock_guard<mutex> lk(log_q->mt);
            log_q->q.push("TS " + to_string(time));
        }
        main_q->cv.notify_one();
        log_q->cv.notify_one();
    
        ++time;
        std::this_thread::sleep_for(1s);
    }
}

void reader(shared_ptr<Stream> main_q) {
    size_t i = 0;
    while (true) {
        {
            lock_guard<mutex> lk(main_q->mt);
            main_q->q.push(to_string(i));
        }
        main_q->cv.notify_one();
        ++i;
        std::this_thread::sleep_for(1s);
    }
}

int main(int argc, const char * argv[]) {
    shared_ptr<Stream> main_q = make_shared<Stream>(), log_q = make_shared<Stream>();
    
    thread log(logger, log_q);
    thread time(timer, log_q, main_q);
    thread input(reader, main_q);

    string cur_t;
    while(true) {
        std::unique_lock<std::mutex> lk(main_q->mt);
        main_q->cv.wait(lk, [&main_q]{return !main_q->q.empty();});
        string message = main_q->q.front();
        main_q->q.pop();
        lk.unlock();
        
        if (message.find("TS") != std::string::npos) {
            cur_t = message.substr(3);
        } else {
            {
                lock_guard<mutex> lk(log_q->mt);
                log_q->q.push(message + " " + cur_t);
            }
            log_q->cv.notify_one();
        }
    }
    log.join();
    time.join();
    input.join();
    
    return 0;
}
