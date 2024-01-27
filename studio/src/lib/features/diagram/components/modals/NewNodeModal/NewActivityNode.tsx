import React from 'react'
import { FormControl, FormLabel, Select, Option, Input } from '@mui/joy'

type Props = {
    object: any
    setObject: (o: any) => void
}

export const NewActivityNode: React.FC<Props> = ({ object, setObject }) => {
    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Role</FormLabel>
                <Select
                    value={object.role}
                    onChange={(_, e) =>
                        setObject((o: any) => ({ ...o, role: e }))
                    }
                    placeholder="Select a role..."
                >
                    <Option value="action">Action</Option>
                    <Option value="control">Control</Option>
                    <Option value="object">Object</Option>
                </Select>
            </FormControl>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type}
                    placeholder="Select a type..."
                    onChange={(_, e) =>
                        setObject((o: any) => ({ ...o, type: e }))
                    }
                >
                    {object.role == 'action' && (
                        <>
                            <Option value="action">Action</Option>
                        </>
                    )}
                    {object.role == 'control' && (
                        <>
                            <Option value="decision">Decision</Option>
                            <Option value="final">Final</Option>
                            <Option value="fork">Fork</Option>
                            <Option value="initial">Initial</Option>
                            <Option value="join">Join</Option>
                            <Option value="merge">Merge</Option>
                        </>
                    )}
                    {object.role == 'object' && (
                        <>
                            <Option value="class">Class</Option>
                            <Option value="buffer">Buffer</Option>
                            <Option value="pin">Pin</Option>
                        </>
                    )}
                </Select>
            </FormControl>
            {object.type == 'action' && (
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
                        placeholder={`Name of the ${object.type ?? 'node'}...`}
                    />
                </FormControl>
            )}
        </>
    )
}
