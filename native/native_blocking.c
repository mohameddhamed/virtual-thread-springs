#include <jni.h>
#include <errno.h>
#include <time.h>

JNIEXPORT void JNICALL
Java_com_thesis_virtualthreadsdemo_service_NativeBlockingService_nativeSleep(JNIEnv *env, jobject self, jlong sleep_millis) {
    (void) env;
    (void) self;

    struct timespec remaining = {
        .tv_sec = (time_t) (sleep_millis / 1000),
        .tv_nsec = (long) ((sleep_millis % 1000) * 1000000L)
    };

    while (nanosleep(&remaining, &remaining) == -1 && errno == EINTR) {
        /* Resume the bounded sleep if a signal interrupts it. */
    }
}

JNIEXPORT void JNICALL
Java_com_thesis_virtualthreadsdemo_service_NativeBlockingService_nativeNoop(JNIEnv *env, jobject self) {
    (void) env;
    (void) self;
}
