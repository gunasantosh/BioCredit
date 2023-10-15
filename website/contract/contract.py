import beaker
import pyteal as pt
from beaker.lib import storage
from beaker.decorators import Authorize

class MyAppState:
    noOfDays = beaker.GlobalStateValue(pt.TealType.uint64, default=pt.Int(0))
    lastTimestamp = beaker.GlobalStateValue(
        pt.TealType.uint64, default=pt.Int(0))
    lastDate = beaker.GlobalStateValue(
        pt.TealType.bytes)
    lastHash = beaker.GlobalStateValue(
        pt.TealType.bytes)
    lastCid = beaker.GlobalStateValue(
        pt.TealType.bytes)
    day = storage.BoxMapping(pt.abi.String, pt.abi.DynamicBytes)


app = beaker.Application('BioCredit', state=MyAppState())


@app.create
def create():
    return app.initialize_global_state()

@app.external(authorize=Authorize.only(pt.Global.creator_address()))
def add_dayhash(date:pt.abi.String,hash:pt.abi.String,cid:pt.abi.String,*,output:pt.abi.String):
    return pt.If(
        app.state.day[date.get()].exists()
        ).Then(
        output.set(pt.Bytes("Hash Already Exists with this Date"))
        ).Else(
        app.state.day[date.get()].set(pt.Concat(pt.Bytes("{'lastDate':'"),app.state.lastDate.get(),pt.Bytes("','lastHash':'"),app.state.lastHash.get(),pt.Bytes("','lastCid':'"),app.state.lastCid.get(),pt.Bytes("','CurrentCid':'"),cid.get(),pt.Bytes("'}"))),
        app.state.lastHash.set(hash.get()),
        app.state.lastDate.set(date.get()),
        app.state.lastCid.set(cid.get()),
        app.state.lastTimestamp.set(pt.Global.latest_timestamp()),
        app.state.noOfDays.increment(),
        output.set(pt.Bytes('Updated Hash Successfully.!!')),
        )

@app.external
def get_hash_by_date(date:pt.abi.String,*,output:pt.abi.DynamicBytes):
    return pt.If(
        app.state.day[date.get()].exists()
        ).Then(
        app.state.day[date.get()].store_into(output)
        ,pt.Approve()
        ).Else(
        output.set(pt.Bytes('No Hash Available For This Date.!!')),
        pt.Reject()
        )


# Rest of the code...
if __name__ == '__main__':
    spec = app.build()
    spec.export('artifacts')








