from pyModbusTCP.client import ModbusClient

# TCP auto connect on modbus request, close after it
c = ModbusClient(host="192.168.3.18", auto_open=True, debug=True)
print(c)
if c.open():
    regs = c.read_holding_registers(0, 2)
    c.close()