# coding: utf-8
# Copyright (c) Materials Virtual Lab
# Distributed under the terms of the BSD License.

"""This module provides function to process data and unify the data format."""

import numpy as np
import pandas as pd
from pymatgen import Structure


def doc_from(structure, energy=None, force=None, stress=None):
    """
    Method to convert structure and its properties into doc
    format for further processing. If properties are None, zeros
    array will be used.

    Args:
        structure (Structure): Pymatgen Structure object.
        energy (float): The total energy of the structure.
        force (np.array): The (m, 3) forces array of the structure
            where m is the number of atoms in structure.
        stress (list/np.array): The (6, ) stresses array of the
            structure.
    Returns:
        (dict)
    """
    energy = energy if energy else 0.0                                  # 没有传入参数的话，能量、力、应力都设为0
    force = force if force else np.zeros((len(structure), 3))
    stress = stress if stress else np.zeros(6)
    outputs = dict(energy=energy, forces=force,                         # 将三者整理为一个字典
                   virial_stress=stress)
    doc = dict(structure=structure.as_dict(),                           # 最终输出的结构信息的格式，as_dict结果是什么？
               num_atoms=len(structure),
               outputs=outputs)
    return doc


def pool_from(structures, energies=None, forces=None, stresses=None):
    """
    Method to convert structures and their properties in to
    datapool format. 将多个结构转换

    Args:
        structures ([Structure]): The list of Pymatgen Structure object.
        energies ([float]): The list of total energies of each structure
            in structures list.
        forces ([np.array]): List of (m, 3) forces array of each structure
            with m atoms in structures list. m can be varied with each
            single structure case.
        stresses (list): List of (6, ) virial stresses of each
            structure in structures list.
    Returns:
        ([dict])
    """
    energies = energies if energies else [None] * len(structures)
    forces = forces if forces else [None] * len(structures)
    stresses = stresses if stresses else [None] * len(structures)
    datapool = [doc_from(structure, energy, force, stress)
                for structure, energy, force, stress
                in zip(structures, energies, forces, stresses)]
    return datapool


def convert_docs(docs, include_stress=False, **kwargs):
    """
    Method to convert a list of docs into objects, e.g.,
    Structure and DataFrame. 重新整理结构数据，返回pymatgen中的Structure对象和pandas的DataFrame对象
    Args:
        docs ([dict]): List of docs. Each doc should have the same
            format as one returned from .dft.parse_dir.
        include_stress (bool): Whether to include stress.
    Returns:
        A list of structures, and a DataFrame with energy and force
        data in 'y_orig' column, data type ('energy' or 'force') in
        'dtype' column, No. of atoms in 'n' column sharing the same row
        of energy data while 'n' being 1 for the rows of force data.
    """
    structures, y_orig, n, dtype = [], [], [], []
    for d in docs:
        if isinstance(d['structure'], dict):
            structure = Structure.from_dict(d['structure'])
        else:
            structure = d['structure']
        outputs = d['outputs']
        force_arr = np.array(outputs['forces'])
        assert force_arr.shape == (len(structure), 3), \
            'Wrong force array not matching structure'
        force_arr = force_arr.ravel()                           # 将数组维度拉为一维数组

        if include_stress:
            stress_arr = np.array(outputs['virial_stress'])
            y = np.concatenate(([outputs['energy']], force_arr, stress_arr))
            n.append(np.insert(np.ones(len(y) - 1), 0, d['num_atoms']))
            dtype.extend(['energy'] + ['force'] * len(force_arr) + ['stress'] * 6)
        else:
            y = np.concatenate(([outputs['energy']], force_arr))
            n.append(np.insert(np.ones(len(y) - 1), 0, d['num_atoms']))
            dtype.extend(['energy'] + ['force'] * len(force_arr))
        y_orig.append(y)
        structures.append(structure)
    df = pd.DataFrame(dict(y_orig=np.concatenate(y_orig), n=np.concatenate(n),
                           dtype=dtype))
    for k, v in kwargs.items():
        df[k] = v
    return structures, df
