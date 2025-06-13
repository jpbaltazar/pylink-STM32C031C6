import time
import pylink

# Flash register addresses for STM32C031C6
FLASH_KEY = 0x40022008
FLASH_OPTKEY = 0x4002200C
FLASH_SR = 0x40022010
FLASH_CR = 0x40022014
FLASH_OPTR = 0x40022020

# Keys for unlocking flash and option bytes
KEY_1 = 0x45670123
KEY_2 = 0xCDEF89AB
OPTKEY_1 = 0x08192A3B
OPTKEY_2 = 0x4C5D6E7F

# Control register values
DEFAULT_CR = 0xFFFFFEAA
# FDCAN_BL_CK   11
# IRHEN         1
# NRST_MODE     11
# NBOOT0        1
# NBOOT1        1
# NBOOT_SEL     1

TARGET_CR = 0xEEFFFEAA #0xFEFFFEAA
# FDCAN_BL_CK   11
# IRHEN         1
# NRST_MODE     11 -> 00
# NBOOT0        1
# NBOOT1        1
# NBOOT_SEL     0

def openJLink(jlink: pylink.JLink):
    """Open and configure JLink connection"""
    jlink.open()
    jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
    # Updated connect method - removed speed parameter, using separate method
    jlink.connect('STM32C031C6', verbose=True)
    jlink.set_speed(4000)  # Set speed separately

def waitUntilNotBusy(jlink: pylink.JLink):
    """Wait until flash is not busy"""
    time.sleep(0.1)
    retries = 3
    for _ in range(retries):
        status = jlink.memory_read32(FLASH_SR, 1)[0]
        busy = status & (1 << 16)
        if not busy:
            break
        time.sleep(0.1)

def setNBootSel():
    """Set nBootSel bit to 0 in option bytes"""
    jlink = pylink.JLink()
    
    try:
        openJLink(jlink)
        jlink.reset(halt=True)
        
        # Check if the flash is locked
        status = jlink.memory_read32(FLASH_CR, 1)[0]
        if status & 0xC0000000:
            print('Flash/OB are locked')
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
        
        # Start the option byte loading
        jlink.memory_write32(FLASH_CR, [0x00020000])
        waitUntilNotBusy(jlink)
        
        # Load the option bytes
        jlink.memory_write32(FLASH_CR, [0x08000000])
        time.sleep(0.1)
        
        # Close and reopen connection due to reset
        jlink.close()
        time.sleep(0.1)
        openJLink(jlink)
        
        # Lock the flash and OB again
        jlink.memory_write32(FLASH_CR, [0xC0000000])
        time.sleep(0.1)
        
        jlink.reset(halt=False)
        
    finally:
        jlink.close()

def checkNBootSel():
    """Check current nBootSel value"""
    jlink = pylink.JLink()
    
    try:
        jlink.open()
        jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
        jlink.connect('STM32C031C6')
        jlink.reset(halt=True)
        
        # Read the value from the option bytes register
        value = jlink.memory_read32(FLASH_OPTR, 1)[0]
        print('NBootSel value: 0x%08X' % value)
        
        jlink.reset(halt=False)
        
    finally:
        jlink.close()

# Main execution
if __name__ == "__main__":
    checkNBootSel()
    # Uncomment the lines below to set nBootSel
    setNBootSel()
    checkNBootSel()
