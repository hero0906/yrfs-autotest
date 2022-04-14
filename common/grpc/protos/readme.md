# use new agent.proto file
# update grpc code
mkdir -p code
python -m grpc_tools.protoc -I. --python_out=./code/ --grpc_python_out=./code/  agent.proto
