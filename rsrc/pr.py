def listen_dmx():
    import gc

    from micropython import alloc_emergency_exception_buf, mem_info

    import config
    import dmx512_rx
    from config import EMERGENCY_EXCEPTION_BUFFER, GC_THRESHOLD

    # Environment
    gc.threshold(GC_THRESHOLD)  # Run Garbage collection everytime 16KB is allocated
    alloc_emergency_exception_buf(EMERGENCY_EXCEPTION_BUFFER)  # Allocate Emergency Exception Buffer

    def dmx_callback(data):
        print(f'Got data: \n{data}')

    dmx = dmx512_rx.DMX(config.DMX_ADDRESS, config.DMX_CHANNELS, config.RX_PIN, update_callback=dmx_callback)
    print("INFO: Starting Main Loop")
    while True:
        if dmx.loop() == 0:  # If 0 we have been offline for an extended period
            print('OFFLINE')
