from ubluetooth import BLE, UUID, FLAG_NOTIFY, FLAG_READ, FLAG_WRITE
from micropython import const
import ubluetooth
import ubinascii
import time
import sys
import machine


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)
#_IRQ_PASSKEY_ACTION= const(32)  #manual entries. Probably to be removed.

_GATTS_NO_ERROR = const(0x00)
_GATTS_ERROR_READ_NOT_PERMITTED = const(0x02)
_GATTS_ERROR_WRITE_NOT_PERMITTED = const(0x03)
_GATTS_ERROR_INSUFFICIENT_AUTHENTICATION = const(0x05)
_GATTS_ERROR_INSUFFICIENT_AUTHORIZATION = const(0x08)
_GATTS_ERROR_INSUFFICIENT_ENCRYPTION = const(0x0f)

_PASSKEY_ACTION_NONE = const(0)
_PASSKEY_ACTION_INPUT = const(2)
_PASSKEY_ACTION_DISPLAY = const(3)
_PASSKEY_ACTION_NUMERIC_COMPARISON = const(4)


UUID_NORDIC_UART = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#Global ListOfAddr()
ListOfAddr = []
ListOfAddrType = []

waiting_events = {}
TIMEOUT_MS = 99000




# ============================================================================================================================================

def bt_irq(event, data):
    """ Full BLE event handler. """
    #print(' ==== ')
    #print(' Event : ', event )
    #print(' ==== ')    
    
    if event == _IRQ_CENTRAL_CONNECT:
        # A central has connected to this peripheral.
        conn_handle, addr_type, addr = data
        
    elif event == _IRQ_CENTRAL_DISCONNECT:
        # A central has disconnected from this peripheral.
        conn_handle, addr_type, addr = data
        
    elif event == _IRQ_GATTS_WRITE:
        # A client has written to this characteristic or descriptor.
        conn_handle, attr_handle = data
        
    elif event == _IRQ_GATTS_READ_REQUEST:
        # A client has issued a read. Note: this is only supported on STM32.
        # Return a non-zero integer to deny the read (see below), or zero (or None)
        # to accept the read.
        conn_handle, attr_handle = data

    elif event == _IRQ_SCAN_RESULT:
        # A single scan result.
        addr_type, addr, adv_type, rssi, adv_data = data

        connected_addr = bytes(addr)
        myaddresstype = addr_type
        myskip='No'
        
        
        # testing signql strength
        if rssi < -90 :  # ignore signals too weak and instable
            myskip='signal too weak.'
            
        elif adv_type not in [0,1]:  #show only connectable devices    
            myskip='cannot get connected to.'
        
        # do not re-connect a previous address
        y = len(ListOfAddr)
        for x in range(0, y):
            if (x > 0) :
                for z in range(0, x):
                    if (ListOfAddr[x] == ListOfAddr[z]) :
                        myskip='already tried to connect to.'
                        break
                    
                    
        print('type:{}      addr:{}     connectable type:{}    rssi:{}    data:{}'.format(addr_type, ubinascii.hexlify(addr), adv_type, rssi, ubinascii.hexlify(adv_data)))
        
        if myskip != 'No': 
            print('Will skip because ', myskip)
            print('')
                    
        # ======================================================================================================================================================
        # all the rest is only for brand new addresses
        if myskip == 'No' :    # otherwise it was already try to connect to.
            ListOfAddr.append(connected_addr)
            ListOfAddrType.append(addr_type)

            # Lets print the details of connectable devices
            print('============================================================================================')
            mystringaddr= str(ubinascii.hexlify(addr))
            MACadd=(mystringaddr[2:4]).upper()
            MACadd= MACadd + ':' + (mystringaddr[4:6]).upper()
            MACadd= MACadd + ':' + (mystringaddr[6:8]).upper()
            MACadd= MACadd + ':' + (mystringaddr[8:10]).upper()
            MACadd= MACadd + ':' + (mystringaddr[10:12]).upper()
            MACadd= MACadd + ':' + (mystringaddr[12:14]).upper()
            print('randomized MAC address :     ' , MACadd)
            
            if adv_type == 0:
                print('0x00 - ADV_IND - connectable and scannable undirected advertising ')
            elif adv_type == 1:
                print('0x01 - ADV_DIRECT_IND - connectable directed advertising ')
            elif adv_type == 2:
                print('0x02 - ADV_SCAN_IND - scannable undirected advertising ')
            elif adv_type == 3:
                print('0x03 - ADV_NONCONN_IND - non-connectable undirected advertising ')
            elif adv_type == 4:
                print('0x04 - SCAN_RSP - scan response ')
           
            print('type:{}      addr:{}     connectable type:{}    rssi:{}    data:{}'.format(addr_type, ubinascii.hexlify(addr), adv_type, rssi, ubinascii.hexlify(adv_data)))
            print( 'bytes(addr) :', bytes(addr) )
            print( ' ')
            
            # Lets try and connect
            bt.gap_connect(myaddresstype, connected_addr)
            wait_for_event(_IRQ_PERIPHERAL_CONNECT, TIMEOUT_MS)
            #print(conn_handle)
            time.sleep(2)



            if  True:    # conn_handle != 999 => no coonection error
                
                # Discover services.
                print ( 'Lets check which services are offered.' )
                bt.gattc_discover_services(0)
                # For each service discovered, the _IRQ_GATTC_SERVICE_RESULT event will be raised, followed by _IRQ_GATTC_SERVICE_DONE on completion.
                # time.sleep(3)
            
                # Discover services characteristics
                bt.gattc_discover_characteristics(0, 11, 65535)
                # For each characteristic discovered, the _IRQ_GATTC_CHARACTERISTIC_RESULT event will be raised, followed by _IRQ_GATTC_CHARACTERISTIC_DONE on completion.
                # conn_handle = wait_for_event(_IRQ_GATTC_CHARACTERISTIC_DONE, TIMEOUT_MS)
                
                # Discover services characteristics descriptors
                #bt.gattc_discover_descriptors(conn_handle, start_handle=1, end_handle=0xffff)
                # For each descriptor discovered, the _IRQ_GATTC_DESCRIPTOR_RESULT event will be raised, followed by _IRQ_GATTC_DESCRIPTOR_DONE on completion.
                #conn_handle = wait_for_event(_IRQ_GATTC_DESCRIPTOR_DONE, TIMEOUT_MS)
                


                conn_handle = wait_for_event(_IRQ_GATTC_SERVICE_DONE, TIMEOUT_MS)
                
                
                
                # Disconnect from peripheral.
                bt.gap_disconnect(conn_handle)
                conn_handle = wait_for_event(_IRQ_PERIPHERAL_DISCONNECT, TIMEOUT_MS)
                #time.sleep(2)  #without spleeping a bit the programm crashes. Not too sure why.

            else :
                #print('could not connect.')
                pass
       

        
    elif event == _IRQ_SCAN_DONE:
        # Scan duration finished or manually stopped.
        print(' *** Scan done. ***')
        print(' ')
        pass
           
    
    elif event == _IRQ_PERIPHERAL_CONNECT:
        # A successful gap_connect().
        print ( ' ')
        print ( ' ')
        print ( '==================================================================================================================================================================== ')
        
        # Connect to peripheral
        print ( 'Yehhhhhhhhhh. I am connected to a peripheral.' )
        conn_handle, addr_type, addr = data
        print ( '..... _IRQ_PERIPHERAL_CONNECT   ',  conn_handle, addr_type, bytes(addr) )
       
        
    elif event == _IRQ_PERIPHERAL_DISCONNECT:
        # Connected peripheral has disconnected.
        conn_handle, addr_type, addr = data
        print ( '..... _IRQ_PERIPHERAL_DISCONNECT', conn_handle, addr_type, bytes(addr) )
        print ( '   ')
        
    elif event == _IRQ_GATTC_SERVICE_RESULT:
        # Called for each service found by gattc_discover_services().
        conn_handle, start_handle, end_handle, uuid = data
        print ( '             ..... _IRQ_GATTC_SERVICE_RESULT :', conn_handle, start_handle, end_handle, uuid  )
         
    elif event == _IRQ_GATTC_SERVICE_DONE:
        # Called once service discovery is complete.
        # Note: Status will be zero on success, implementation-specific value otherwise.
        conn_handle, status = data
        print( '             ..... _IRQ_GATTC_SERVICE_DONE :', conn_handle, status) 
        
    elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
        # Called for each characteristic found by gattc_discover_services().
        conn_handle, def_handle, value_handle, properties, uuid = data
        print( '                  .....IRQ_GATTC_CHARACTERISTIC_RESULT :', conn_handle, def_handle, value_handle, properties, uuid )
        
        
    elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
        # Called once service discovery is complete.
        # Note: Status will be zero on success, implementation-specific value otherwise.
        conn_handle, status = data
        print('                       ..... _IRQ_GATTC_CHARACTERISTIC_DONE', conn_handle, status)
        
    elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
        # Called for each descriptor found by gattc_discover_descriptors().
        conn_handle, dsc_handle, uuid = data
        print('                                     ..... _IRQ_GATTC_DESCRIPTOR_RESULT', conn_handle, dsc_handle, uuid)
        
    elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
        # Called once service discovery is complete.
        # Note: Status will be zero on success, implementation-specific value otherwise.
        conn_handle, status = data
        print('                                     ..... _IRQ_GATTC_DESCRIPTOR_DONE', conn_handle, status)
        
    elif event == _IRQ_GATTC_READ_RESULT:
        # A gattc_read() has completed.
        conn_handle, value_handle, char_data = data
        
    elif event == _IRQ_GATTC_READ_DONE:
        # A gattc_read() has completed.
        # Note: The value_handle will be zero on btstack (but present on NimBLE).
        # Note: Status will be zero on success, implementation-specific value otherwise.
        conn_handle, value_handle, status = data
        
    elif event == _IRQ_GATTC_WRITE_DONE:
        # A gattc_write() has completed.
        # Note: The value_handle will be zero on btstack (but present on NimBLE).
        # Note: Status will be zero on success, implementation-specific value otherwise.
        conn_handle, value_handle, status = data
        
    elif event == _IRQ_GATTC_NOTIFY:
        # A server has sent a notify request.
        conn_handle, value_handle, notify_data = data
        
    elif event == _IRQ_GATTC_INDICATE:
        # A server has sent an indicate request.
        conn_handle, value_handle, notify_data = data
        
    elif event == _IRQ_GATTS_INDICATE_DONE:
        # A client has acknowledged the indication.
        # Note: Status will be zero on successful acknowledgment, implementation-specific value otherwise.
        conn_handle, value_handle, status = data
        
    elif event == _IRQ_MTU_EXCHANGED:
        # ATT MTU exchange complete (either initiated by us or the remote device).
        conn_handle, mtu = data
        
    elif event == _IRQ_L2CAP_ACCEPT:
        # A new channel has been accepted.
        # Return a non-zero integer to reject the connection, or zero (or None) to accept.
        conn_handle, cid, psm, our_mtu, peer_mtu = data
        
    elif event == _IRQ_L2CAP_CONNECT:
        # A new channel is now connected (either as a result of connecting or accepting).
        conn_handle, cid, psm, our_mtu, peer_mtu = data
        
    elif event == _IRQ_L2CAP_DISCONNECT:
        # Existing channel has disconnected (status is zero), or a connection attempt failed (non-zero status).
        conn_handle, cid, psm, status = data
        
    elif event == _IRQ_L2CAP_RECV:
        # New data is available on the channel. Use l2cap_recvinto to read.
        conn_handle, cid = data
        
    elif event == _IRQ_L2CAP_SEND_READY:
        # A previous l2cap_send that returned False has now completed and the channel is ready to send again.
        # If status is non-zero, then the transmit buffer overflowed and the application should re-send the data.
        conn_handle, cid, status = data
        
    elif event == _IRQ_CONNECTION_UPDATE:
        # The remote device has updated connection parameters.
        conn_handle, conn_interval, conn_latency, supervision_timeout, status = data
        
    elif event == _IRQ_ENCRYPTION_UPDATE:
        # The encryption state has changed (likely as a result of pairing or bonding).
        conn_handle, encrypted, authenticated, bonded, key_size = data
        
    elif event == _IRQ_GET_SECRET:
        # Return a stored secret.
        # If key is None, return the index'th value of this sec_type.
        # Otherwise return the corresponding value for this sec_type and key.
        sec_type, index, key = data
        return value
    
    elif event == _IRQ_SET_SECRET:
        # Save a secret to the store for this sec_type and key.
        sec_type, key, value = data
        return True
    
    elif event == _IRQ_PASSKEY_ACTION:
        # Respond to a passkey request during pairing.
        # See gap_passkey() for details.
        # action will be an action that is compatible with the configured "io" config.
        # passkey will be non-zero if action is "numeric comparison".
        conn_handle, action, passkey = data
        
# ============================================================================================================================================





# =====================================================================

def adv_decode(adv_type, data):
    """ ADV decode """
    i = 0
    while i + 1 < len(data):
        if data[i + 1] == adv_type:
            return data[i + 2:i + data[i] + 1]
        i += 1 + data[i]
    return None

def adv_decode_name(data):
    """ ADV decode name """
    n = adv_decode(0x09, data)
    if n:
        return n.decode("utf-8")
    return data

def adv_encode_name(name):
    """ ADV encode name """
    name = bytes(name, "ascii")
    return bytearray((len(name) + 1, 0x09)) + name

def register_services():
    """ Register UART services. Run on peripheral only. """
    UART_UUID = ubluetooth.UUID(UUID_NORDIC_UART)
    UART_TX = (ubluetooth.UUID(UUID_NORDIC_UART), ubluetooth.FLAG_READ | ubluetooth.FLAG_NOTIFY, )
    UART_RX = (ubluetooth.UUID(UUID_NORDIC_UART), ubluetooth.FLAG_WRITE,)
    UART_SERVICE = (UART_UUID, (UART_TX, UART_RX,),)
    SERVICES = (UART_SERVICE,)
    ((tx, rx,), ) = ble.gatts_register_services(SERVICES)
    print("tx", tx, "rx:", rx)



# ========================================================

def wait_for_event(event, timeout_ms):
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
        if event in waiting_events:
            return waiting_events.pop(event)
        #machine.idle()
    
    # raise ValueError("Timeout waiting for {}".format(event))
    if event == 7 :
        print('raise ValueError Timeout waiting for {}'.format(event) , 'No connection')
    elif event == 10 :
        print('raise ValueError Timeout waiting for {}'.format(event) , 'GATTC service done.')
    else :
        print('raise ValueError Timeout waiting for {}'.format(event))
    return 999       


# ==== Main ==========================================

print('')
print('         ==================              ==================         ==================              ==================               ')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')
print('')



bt = BLE()
bt.active(True)
bt.irq(bt_irq)

# Back on the central device, we can now scan the environment using ble.gap_scan() to see if we can detect our social media adversary:
adv_data = "ESP32Emmanuel"
bt.gap_scan(100000, 1280000, 11250)
#bt.gap_scan(None)

print('... Wait for the scan results. Will take a few seconds.' )
print('  ')
print('  ')
print('  ')


