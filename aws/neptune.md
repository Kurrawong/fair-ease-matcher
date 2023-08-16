To load to neptune:
Start a Jupyter notebook (well, server), create a terminal and run the following:
```bash
curl -X POST \
    -H 'Content-Type: application/json' \
    https://bodc.cluster-clc4weqlymzs.ap-southeast-2.neptune.amazonaws.com:8182/loader -d '
    {
      "source" : "s3://bodc-sakb/sakb_statements.nq",
      "format" : "nquads",
      "iamRoleArn" : "arn:aws:iam::090403239536:role/NeptuneLoadFromS3",
      "region" : "ap-southeast-2",
      "failOnError" : "FALSE",
      "parallelism" : "MEDIUM",
      "updateSingleCardinalityProperties" : "FALSE",
      "queueRequest" : "TRUE"
    }'
```


to connect from remote:
Follow this tutorial: https://github.com/m-thirumal/aws-cloud-tutorial/blob/main/neptune/connect_from_local.adoc
1. create EC2 instance w/ SSH keypair, ensure I can remove from local
2. create security group and add 8182 as accessible from my IP
NB for some reason the read only endpoint doesn't seem to work.
3. edit /etc/hosts
4. ssh -i ~/.ssh/bodc-bastion.pem ubuntu@ec2-13-211-139-208.ap-southeast-2.compute.amazonaws.com -N -L 8182:bodc.cluster-clc4weqlymzs.ap-southeast-2.neptune.amazonaws.com:8182
5. test link: https://bodc.cluster-clc4weqlymzs.ap-southeast-2.neptune.amazonaws.com:8182/status
