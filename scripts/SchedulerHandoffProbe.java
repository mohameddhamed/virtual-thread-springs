import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.LockSupport;

/**
 * Exploratory handoff microbenchmark.
 *
 * This measures a two-thread park/unpark handoff, not an isolated OS context
 * switch. Results are mechanism evidence only and must not be translated
 * directly into application throughput.
 */
public final class SchedulerHandoffProbe {
    private static final int WARMUP_ROUNDS = 10_000;
    private static final int MEASURE_ROUNDS = 100_000;
    private static final int REPETITIONS = 5;

    public static void main(String[] args) throws Exception {
        run("platform", false);
        run("virtual", true);
    }

    private static void run(String label, boolean virtual) throws Exception {
        System.out.println(label);
        for (int repetition = 1; repetition <= REPETITIONS; repetition++) {
            handoff(virtual, WARMUP_ROUNDS);
            long elapsed = handoff(virtual, MEASURE_ROUNDS);
            double handoffs = MEASURE_ROUNDS * 2.0;
            System.out.printf(
                    "  repetition=%d total_ms=%.3f ns_per_handoff=%.1f%n",
                    repetition,
                    elapsed / 1_000_000.0,
                    elapsed / handoffs);
        }
    }

    private static long handoff(boolean virtual, int rounds) throws Exception {
        var ready = new CountDownLatch(2);
        var turn = new AtomicInteger(0);
        var firstOther = new AtomicReference<Thread>();
        var secondOther = new AtomicReference<Thread>();
        var first = new HandoffThread(rounds, 0, 1, ready, turn, firstOther);
        var second = new HandoffThread(rounds, 1, 0, ready, turn, secondOther);

        Thread firstThread = virtual
                ? Thread.startVirtualThread(first)
                : new Thread(first, "platform-first");
        Thread secondThread = virtual
                ? Thread.startVirtualThread(second)
                : new Thread(second, "platform-second");
        firstOther.set(secondThread);
        secondOther.set(firstThread);
        if (!virtual) {
            firstThread.start();
            secondThread.start();
        }

        ready.await();
        long start = System.nanoTime();
        LockSupport.unpark(firstThread);
        firstThread.join();
        secondThread.join();
        return System.nanoTime() - start;
    }

    private static final class HandoffThread implements Runnable {
        private final int rounds;
        private final int myTurn;
        private final int nextTurn;
        private final CountDownLatch ready;
        private final AtomicInteger turn;
        private final AtomicReference<Thread> other;

        private HandoffThread(
                int rounds,
                int myTurn,
                int nextTurn,
                CountDownLatch ready,
                AtomicInteger turn,
                AtomicReference<Thread> other) {
            this.rounds = rounds;
            this.myTurn = myTurn;
            this.nextTurn = nextTurn;
            this.ready = ready;
            this.turn = turn;
            this.other = other;
        }

        @Override
        public void run() {
            ready.countDown();
            for (int i = 0; i < rounds; i++) {
                while (turn.get() != myTurn) {
                    LockSupport.park();
                }
                turn.set(nextTurn);
                LockSupport.unpark(other.get());
            }
        }
    }
}
