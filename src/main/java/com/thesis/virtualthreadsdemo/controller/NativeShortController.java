package com.thesis.virtualthreadsdemo.controller;

import com.thesis.virtualthreadsdemo.service.NativeBlockingService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/native-short")
@ConditionalOnProperty(prefix = "demo.native", name = "enabled", havingValue = "true")
public class NativeShortController {

    private final NativeBlockingService nativeBlockingService;

    public NativeShortController(NativeBlockingService nativeBlockingService) {
        this.nativeBlockingService = nativeBlockingService;
    }

    @GetMapping
    public String noOp() {
        return nativeBlockingService.noOp();
    }
}
