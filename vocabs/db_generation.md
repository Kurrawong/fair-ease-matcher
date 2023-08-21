

```shell
docker run \
   -v <host_db_dir>:/newdb \
   --mount type=bind,source=<host_data_dir>,target=/rdf \
   -e DATASET=mydataset \
   tdb-generation:<image_version>
```

my example:

```shell
docker run \
   -v fair-ease-volume:/newdb \
   --mount type=bind,source=/home/david/PycharmProjects/BODC-matcher/vocabs,target=/rdf \
   -e DATASET=fair-ease \
   tdb-generation:0.1.8
```
