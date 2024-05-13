import time
import pylink

FLASH_KEY = 0x40022008
FLASH_OPTKEY = 0x4002200C

FLASH_SR = 0x40022010
FLASH_CR = 0x40022014
FLASH_OPTR = 0x40022020

KEY_1 = 0x45670123
KEY_2 = 0xCDEF89AB

OPTKEY_1 = 0x08192A3B
OPTKEY_2 = 0x4C5D6E7F

DEFAULT_CR = 0xFFFFFEAA
TARGET_CR = 0xFEFFFEAA

def openJLink(jlink: pylink.JLink):
    jlink.open()
    jlink.set_tif(pylink.JLinkInterfaces.SWD)
    jlink.connect('STM32C031C6', speed=4000, verbose=True)

def waitUntilNotBusy(jlink: pylink.JLink):
    time.sleep(0.1)

    retries = 3
    for _ in range(retries):
        status = jlink.memory_read32(FLASH_SR, 1)[0]
        busy = status & (1 << 16)
        if not busy:
            break
        time.sleep(0.1)

def setNBootSel():
    jlink = pylink.JLink()
    openJLink(jlink)
    jlink.reset(halt=True)

    # Check if the flash is locked
    status = jlink.memory_read32(FLASH_CR, 1)[0]
    if status & 0xC0000000:
        print('Flash is locked')
    
        # Unlock the flash
        jlink.memory_write32(FLASH_KEY, [KEY_1])
        time.sleep(0.01)
        jlink.memory_write32(FLASH_KEY, [KEY_2])
        time.sleep(0.01)

        # Unlock the option bytes
        jlink.memory_write32(FLASH_OPTKEY, [OPTKEY_1])
        time.sleep(0.01)
        jlink.memory_write32(FLASH_OPTKEY, [OPTKEY_2])
        time.sleep(0.01)
    else:
        print('Flash already unlocked')

    # Set nBootSel to 0
    jlink.memory_write32(FLASH_OPTR, [TARGET_CR])
    waitUntilNotBusy(jlink)

    # start the option byte loading
    jlink.memory_write32(FLASH_CR, [0x00020000])
    waitUntilNotBusy(jlink)

    # Load the option bytes
    jlink.memory_write32(FLASH_CR, [0x08000000])
    time.sleep(0.1)

    # Needs to close and open the JLink connection because loading the option bytes resets the stm32
    jlink.close()
    time.sleep(0.1)
    openJLink(jlink)

    # Lock the flash again
    jlink.memory_write32(FLASH_CR, [0xC0000000])
    time.sleep(0.1)

    jlink.reset(halt=False)
    jlink.close()

def checkNBootSel():
    jlink = pylink.JLink()
    jlink.open()
    jlink.set_tif(pylink.JLinkInterfaces.SWD)
    jlink.connect('STM32C031C6', speed=4000)
    jlink.reset(halt=True)

    # Read the value from the specified address
    value = jlink.memory_read32(0x40022020, 1)[0]
    print('NBootSel value: 0x%08X' % value)

    jlink.reset(halt=False)
    jlink.close()

checkNBootSel()
setNBootSel()
checkNBootSel()