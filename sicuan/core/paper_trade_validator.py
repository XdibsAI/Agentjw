class PaperTradeValidator:


    def validate(
        self,
        before,
        after
    ):

        before_pnl = before.get(
            "paper_pnl",
            0
        )

        after_pnl = after.get(
            "paper_pnl",
            0
        )


        return {

            "before_pnl":
                before_pnl,

            "after_pnl":
                after_pnl,

            "pnl_delta":
                after_pnl - before_pnl,


            "accepted":
                after_pnl >= before_pnl
        }
