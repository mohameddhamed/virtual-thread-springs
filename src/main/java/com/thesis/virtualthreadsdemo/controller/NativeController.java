package com.thesis.virtualthreadsdemo.controller;

import com.thesis.virtualthreadsdemo.service.NativeBlockingService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/native")
@ConditionalOnProperty(prefix = "demo.native", name = "enabled", havingValue = "true")
public class NativeController {

    private final NativeBlockingService nativeBlockingService;

    public NativeController(NativeBlockingService nativeBlockingService) {
        this.nativeBlockingService = nativeBlockingService;
    }

    @GetMapping
    public String block() {
        return nativeBlockingService.block();
    }

}
