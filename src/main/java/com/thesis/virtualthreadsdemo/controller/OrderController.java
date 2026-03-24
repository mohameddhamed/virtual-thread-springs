package com.thesis.virtualthreadsdemo.controller;

// TODO: Endpoint to simulate slow order retrieval
// Will call service layer that uses blocking JDBC + ThreadLocal
// Expected to demonstrate thread pinning under Virtual Threads