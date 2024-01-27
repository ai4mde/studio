import React from 'react'
import { FormControl, FormLabel, Select, Option, Input } from '@mui/joy'

type Props = {
    object: any
    setObject: (o: any) => void
}

export const NewActivityConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type}
                    onChange={(_, v) =>
                        setObject((o: any) => ({
                            ...o,
                            type: v,
                        }))
                    }
                >
                    <Option value="association" label="Association">
                        Association
                    </Option>
                    <Option value="generalization" label="Generalization">
                        Generalization
                    </Option>
                    <Option value="composition" label="Composition">
                        Composition
                    </Option>
                </Select>
            </FormControl>
            {(object.type == 'association' ||
                object.type == 'generalization') && (
                <>
                    <div className="w-full flex flex-row gap-2 justify-between items-center">
                        <FormControl size="sm">
                            <FormLabel>Label From</FormLabel>
                            <Input></Input>
                        </FormControl>
                        <FormControl size="sm">
                            <FormLabel>To</FormLabel>
                            <Input></Input>
                        </FormControl>
                    </div>
                    <div className="w-full flex flex-row gap-2 justify-between items-center">
                        <FormControl size="sm">
                            <FormLabel>Multiplicity From</FormLabel>
                            <Input></Input>
                        </FormControl>
                        <FormControl size="sm">
                            <FormLabel>To</FormLabel>
                            <Input></Input>
                        </FormControl>
                    </div>
                </>
            )}
        </>
    )
}

export default NewActivityConnection
