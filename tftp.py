"""
TFTP Module.
"""

import socket
import sys
import threading
########################################################################
#                          COMMON ROUTINES                             #
########################################################################

# todo

########################################################################
#                             SERVER SIDE                              #
########################################################################

request_port = 6969
host = ""


def runServer(addr, timeout, thread):

	transfert_port = addr[1]
	# creating 2 sockets
	# the first is ONLY for recieving requests
	# the second is for file transfering
	socket_request = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	socket_request.bind((host,request_port))
	
	socket_transfert = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	socket_transfert.bind((host,transfert_port))

	print("Listening on {} for requests...".format(request_port))


	while True :
		# recieving the client's request (RRQ or WRQ), and his id
		request, client_addr = socket_request.recvfrom(512)
		print(request)

		# extracting the info (request type, filename, mode)
		# extracting the opcode
		opcode = request[0:2]
		opcode = int.from_bytes(opcode, byteorder='big')
		# extracting the filename & mode (which will be octet for our case)
		args= request[2:]
		print(args)
		args = args.split(b'\x00')
		filename = args[0].decode('ascii')
		print("filename",filename)
		targetname = args[1].decode('ascii') #args[1].decode('ascii')
		print("targetname",targetname)
		mode = args[2].decode('ascii')
		print("mode",mode)
		blksize = int(args[4].decode())
		print("blksize",blksize)

		#ACK0 = b'\x04\x00'
		#socket_transfert.sendto(ACK0,client_addr)


		# Case 1 : Read request (server sending to the client)
		if (opcode == 1):

			# Opening a file with the name filename, with 'r' since we're sending to a client
			file = open(filename, 'rb')

			print("Sending {} to {}".format(filename,addr))

			total_sent = 0
			data = file.read()
			total_size = len(data)
			compteur = 1
			
			# C'est la hess ici, bisous futur Brahim, de la part de Emma aussi :) , UPDATE : Bien joué Brahim

			while total_sent < total_size :
				# the data about to be sent
				if(total_sent + blksize < total_size):
					data_sent = data[total_sent:total_sent+blksize]
					total_sent += blksize

				elif(total_sent + blksize >= total_size):
					data_sent = data[total_sent:]
					total_sent = total_size
				# sending the data to 'addr'

				
				dat = b'\x00\x03' + compteur.to_bytes(2,'big') + bytearray(data_sent)
				print("in loop")
				print(dat)
				socket_transfert.sendto(dat, client_addr)

				# reçu de l'aquittement
				ack = socket_transfert.recv(4)
				opcode = ack[0:2]
				n_block = ack[2:]

				# Gestion des erreurs
				

				compteur += 1

			file.close()
			print(f'{filename} successfully sent to {client_addr} as {targetname}')
			print("Listening on {} for requests...".format(request_port))
			# jusqu'au ici ! courage le sang



		# Case 2 : Write request (server receiving from the client)
		elif(opcode == 2):
			# Sending the ACK0
			ACK0 = b'\x00\x04\x00\x00'
			socket_transfert.sendto(ACK0,client_addr)

			# Opening a file with the name filename, with 'w' since we're receiving from a client
			file = open(targetname, 'wb')
			print("Receiving {} as {} from {} ".format(filename,targetname,addr))
			# a list of to stock all the blocks that we'll receive
			blocks = []
			data_recvd = 0
			block = " "

			while data_recvd % (blksize+4) == 0 and len(block) != 0 :
				block = socket_transfert.recv(blksize+4)
				data_recvd += len(block)
				print(block)

				ack = b'\x00\x04'+block[2:4]
				socket_transfert.sendto(ack,client_addr)
				blocks.append(block[4:])

			content = b''.join(blocks)
			file.write(content)
			file.close()
			print(f'{filename} successfully received from {client_addr} as {targetname}')
			print("Listening on {} for requests...".format(request_port))


	print("Server shutting down...")
	socket_request.close()
	socket_transfert.close()
	pass

########################################################################
#                             CLIENT SIDE                              #
########################################################################


def put(addr, filename, targetname, blksize, timeout):

	socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# socket_client.bind((addr[0],addr[1]))

	# Opening a file with the name filename, with 'r' since we're sending to a client
	file = open(filename, 'rb')

	WRQ = bytearray('\x00\x02{}\x00{}\x00octet\x00blksize\x00{}\x00'.format(filename,targetname,blksize).encode())
	WRQ_MES="[myclient:{} -> myserver:6969] WRQ={}".format(str(addr[1]),WRQ)
	print(WRQ_MES)

	# sending the request to the server
	socket_client.sendto(WRQ,("",request_port))

	# receiving the adress of the server through the ack sent by the server, for put request
	ACK0, transfert_server = socket_client.recvfrom(4)

	total_sent = 0
	data = file.read()
	total_size = len(data)

	compteur = 1

	while total_sent < total_size :
		# the data about to be sent
		if(total_sent + blksize < total_size):
			data_sent = data[total_sent:total_sent+blksize]
			total_sent += blksize

		elif(total_sent + blksize >= total_size):
			data_sent = data[total_sent:]
			total_sent = total_size

		# sending the data to 'addr'
		dat = b'\x00\x03' + compteur.to_bytes(2,'big') + bytearray(data_sent)
		socket_client.sendto(dat,transfert_server)

		# Messages qui s'affiche sur l'écran du client (ACKx et DATx)
		DAT_MES="[myclient:{} -> myserver:{}] DAT{}={}".format(str(addr[1]),str(transfert_server[1]),compteur,dat)
		print(DAT_MES)
		#ACK_MES="[myclient:{} -> myserver:{}] ACK{}=b'\x00\x04\x00\x01{}'".format()
		
		ack = socket_client.recv(4)
		ACK_MES="[myserver:{} -> myclient:{}] ACK{}={}".format(transfert_server[1],addr[1],compteur,ack)
		print(ACK_MES)

		compteur += 1

	file.close()

	pass

########################################################################


def get(addr, filename, targetname, blksize, timeout):
	
	socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# socket_client.bind((addr[0],addr[1]))

	#converting filename from ascii to bytearray
	# creating the targetfile / where to stock what we receive
	file = open(targetname,'wb')

	# sending the get request
	RRQ = bytearray('\x00\x01{}\x00{}\x00octet\x00blksize\x00{}\x00'.format(filename,targetname,blksize).encode())
	RRQ_MES="[myclient:{} -> myserver:6969] RRQ={}".format(str(addr[1]),RRQ)
	print(RRQ_MES)
	socket_client.sendto(RRQ,("",request_port))

	# a list to stock all the blocks that we'll receive
	blocks = []
	data_recvd = 0
	compteur = 1

	# éviter une boucle infinie, car en utlisant que (data_recvd % blksize == 0) comme condition pour le while juste en dessous
	# on peut avoir des problémes si la longueur du fichier est divisible par blksize
	block = " "

	while data_recvd % (blksize+4) == 0 and len(block) != 0 :
		
		block, transfert_server = socket_client.recvfrom(blksize+4) # on rajoute 4 byte vu que l'opcode en rajoute 2 à la taille, et n_block en rajoute 2 aussi
		data_recvd += len(block)

		# Received Data + confirmation message
		DAT_MES="[myserver:{} -> myclient:{}] DAT{}={}".format(transfert_server[1],addr[1],compteur,block)
		print(DAT_MES)


		#ACK acquittement (qu'on renvoie au server contenant le numéro de block reçu qui est block[2:4])
		ACK = b'\x00\x04'+block[2:4]
		ACK_MES="[myclient:{} -> myserver:{}] ACK{}={}".format(addr[1],transfert_server[1],compteur,ACK)
		print(ACK_MES)
		#Envoi de l'acquittement
		socket_client.sendto(ACK,transfert_server)

		compteur += 1
		# on rajoute la data au tableau contenant les blocks reçus
		blocks.append(block[4:])

	content = b''.join(blocks)
	file.write(content)
	file.close()

	pass
	

# EOF
