from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from datetime import datetime as DT
import time

rpcuser = 'quaker_quorum'
rpcpassword = 'franklin_fought_for_continental_cash'
rpcport = 8332
rpcip = '3.134.159.30'

rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpcuser, rpcpassword, rpcip, rpcport))

# # rpc_user and rpc_password are set in the bitcoin.conf file
# best_block_hash = rpc_connection.getbestblockhash()
# # print(rpc_connection.getblock(best_block_hash))
#
# # batch support : print timestamps of blocks 0 to 99 in 2 RPC round-trips:
# commands = [["getblockhash", height] for height in range(1000)]
# block_hashes = rpc_connection.batch_(commands)
# blocks = rpc_connection.batch_([["getblock", h] for h in block_hashes])
# block_times = [block["time"] for block in blocks]
#
# time_stamp = blocks[0]['time']
# time_stame_array = time.localtime(time_stamp)
# utc_time = DT.utcfromtimestamp(time_stamp).strftime("%Y-%m-%d %H:%M:%S")
#
# # for b in blocks:
# #     print(b)
#
# print()
# print(blocks[0]['hash'], end=' ')
# print(time_stamp, end=' ')
# print(utc_time)
#
# for i in range(1000):
#     if blocks[i]['time'] >= 1232100000:
#         print(str(i)+' '+blocks[i]['hash']+' '+str(blocks[i]['time']))
#         break
#
#
