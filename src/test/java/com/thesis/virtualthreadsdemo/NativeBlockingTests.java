package com.thesis.virtualthreadsdemo;

import com.thesis.virtualthreadsdemo.service.NativeBlockingService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
        "demo.native.enabled=true",
        "demo.native.sleep-millis=20"
})
@AutoConfigureMockMvc
class NativeBlockingTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private NativeBlockingService nativeBlockingService;

    @Test
    void nativeEndpointPerformsBoundedBlockingCall() throws Exception {
        long started = System.nanoTime();

        mockMvc.perform(get("/native"))
                .andExpect(status().isOk())
                .andExpect(content().string("Native blocking sleep completed"));

        long elapsedMillis = (System.nanoTime() - started) / 1_000_000;
        assertThat(elapsedMillis).isGreaterThanOrEqualTo(10);
    }

    @Test
    void nativeServiceIsAvailableWhenExplicitlyEnabled() {
        assertThat(nativeBlockingService).isNotNull();
        assertThat(nativeBlockingService.sleepMillis()).isEqualTo(20);
    }

    @Test
    void nativeShortEndpointCallsNoOpWithoutSleeping() throws Exception {
        mockMvc.perform(get("/native-short"))
                .andExpect(status().isOk())
                .andExpect(content().string("Native no-op completed"));
    }
}
