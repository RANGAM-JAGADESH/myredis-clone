def rewrite_aof(db):

    try:

        with open("appendonly.aof", "w") as file:

            for key, value in db.store.items():

                file.write(
                    f"SET {key} {value}\n"
                )

        print("AOF Rewrite Complete")

    except Exception as e:

        print(
            f"AOF Rewrite Error: {e}"
        )