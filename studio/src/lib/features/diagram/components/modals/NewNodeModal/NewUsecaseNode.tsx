import { FormControl, FormLabel, Input, Option, Select } from '@mui/joy'
import React from 'react'

type Props = {
    object: any
    setObject: (o: any) => void
}

export const NewUsecaseNode: React.FC<Props> = ({ object, setObject }) => {
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
                    <Option value="actor" label="Actor">
                        Actor
                    </Option>
                    <Option value="usecase" label="Use Case">
                        Use Case
                    </Option>
                </Select>
            </FormControl>
            <FormControl size="sm" className="w-full">
                <FormLabel>Name</FormLabel>
                <Input
                    value={object.name}
                    onChange={(e) =>
                        setObject((o: any) => ({
                            ...o,
                            name: e.target.value,
                        }))
                    }
                />
            </FormControl>
        </>
    )
}
