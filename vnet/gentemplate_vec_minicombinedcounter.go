// autogenerated: do not edit!
// generated from gentemplate [gentemplate -d Package=vnet -id miniCombinedCounter -d VecType=miniCombinedCounterVec -d Type=miniCombinedCounter github.com/platinasystems/go/elib/vec.tmpl]

// Copyright 2016 Platina Systems, Inc. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package vnet

import (
	"github.com/platinasystems/go/elib"
)

type miniCombinedCounterVec []miniCombinedCounter

func (p *miniCombinedCounterVec) Resize(n uint) {
	old_cap := uint(cap(*p))
	new_len := uint(len(*p)) + n
	if new_len > old_cap {
		new_cap := elib.NextResizeCap(new_len)
		q := make([]miniCombinedCounter, new_len, new_cap)
		copy(q, *p)
		*p = q
	}
	*p = (*p)[:new_len]
}

func (p *miniCombinedCounterVec) validate(new_len uint, zero miniCombinedCounter) *miniCombinedCounter {
	old_cap := uint(cap(*p))
	old_len := uint(len(*p))
	if new_len <= old_cap {
		// Need to reslice to larger length?
		if new_len > old_len {
			*p = (*p)[:new_len]
			for i := old_len; i < new_len; i++ {
				(*p)[i] = zero
			}
		}
		return &(*p)[new_len-1]
	}
	return p.validateSlowPath(zero, old_cap, new_len, old_len)
}

func (p *miniCombinedCounterVec) validateSlowPath(zero miniCombinedCounter, old_cap, new_len, old_len uint) *miniCombinedCounter {
	if new_len > old_cap {
		new_cap := elib.NextResizeCap(new_len)
		q := make([]miniCombinedCounter, new_cap, new_cap)
		copy(q, *p)
		for i := old_len; i < new_cap; i++ {
			q[i] = zero
		}
		*p = q[:new_len]
	}
	if new_len > old_len {
		*p = (*p)[:new_len]
	}
	return &(*p)[new_len-1]
}

func (p *miniCombinedCounterVec) Validate(i uint) *miniCombinedCounter {
	var zero miniCombinedCounter
	return p.validate(i+1, zero)
}

func (p *miniCombinedCounterVec) ValidateInit(i uint, zero miniCombinedCounter) *miniCombinedCounter {
	return p.validate(i+1, zero)
}

func (p *miniCombinedCounterVec) ValidateLen(l uint) (v *miniCombinedCounter) {
	if l > 0 {
		var zero miniCombinedCounter
		v = p.validate(l, zero)
	}
	return
}

func (p *miniCombinedCounterVec) ValidateLenInit(l uint, zero miniCombinedCounter) (v *miniCombinedCounter) {
	if l > 0 {
		v = p.validate(l, zero)
	}
	return
}

func (p *miniCombinedCounterVec) ResetLen() {
	if *p != nil {
		*p = (*p)[:0]
	}
}

func (p miniCombinedCounterVec) Len() uint { return uint(len(p)) }
