db.createUser(
        {
            user: "teamAA",
            pwd: "teamAA",
            roles: [
                {
                    role: "readWrite",
                    db: "DAPPROJECT"
                }
            ]
        }
);