package com.thesis.virtualthreadsdemo.service;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
@ConditionalOnProperty(prefix = "demo.native", name = "enabled", havingValue = "true")
public class NativeBlockingService {

    public static final long DEFAULT_SLEEP_MILLIS = 500L;

    static {
        System.loadLibrary("nativeblocking");
    }

    private final long sleepMillis;

    public NativeBlockingService(
            @Value("${demo.native.sleep-millis:" + DEFAULT_SLEEP_MILLIS + "}") long sleepMillis) {
        if (sleepMillis < 1) {
            throw new IllegalArgumentException("demo.native.sleep-millis must be at least 1");
        }
        this.sleepMillis = sleepMillis;
    }

    private native void nativeSleep(long sleepMillis);

    private native void nativeNoop();

    public String block() {
        nativeSleep(sleepMillis);
        return "Native blocking sleep completed";
    }

    public String noOp() {
        nativeNoop();
        return "Native no-op completed";
    }

    public long sleepMillis() {
        return sleepMillis;
    }
}
