import numpy as np
import theano
import theano.tensor as T
import lasagne
from .dqn_inits import create_NIPS_sprag_init

FLOATX = theano.config.floatX


class DQN_NIPS:
    def __init__(self, network_parms, training_parms):
        network_parms.required(['input_shape', 'output_num'])
        training_parms.required(['learning_rate', 'minibatch_size', 'discount'])

        # setup shared vars
        inp_shape = network_parms.get('input_shape')
        output_num = network_parms.get('output_num')
        minibatch = training_parms.get('minibatch_size')
        self.states_for_training = theano.shared(np.zeros((minibatch, inp_shape[0], inp_shape[1], inp_shape[2]), dtype=FLOATX))
        self.states_tp1 = theano.shared(np.zeros((minibatch, inp_shape[0], inp_shape[1], inp_shape[2]), dtype=FLOATX))
        self.states_for_output = theano.shared(np.zeros((1, inp_shape[0], inp_shape[1], inp_shape[2]), dtype=FLOATX))
        self.truths = theano.shared(np.zeros((minibatch, output_num), dtype=FLOATX))
        self.terminals = theano.shared(np.zeros(minibatch, dtype='int32'))
        self.rewards = theano.shared(np.zeros(minibatch, dtype=FLOATX))
        self.actions = theano.shared(np.zeros(minibatch, dtype='int32'))

        network_dic = create_NIPS_sprag_init(network_parms)
        self.l_in = network_dic['l_in']
        self.l_hid1 = network_dic['l_hid1']
        self.l_hid2 = network_dic['l_hid2']
        self.l_hid3 = network_dic['l_hid3']
        self.l_out = network_dic['l_out']

        # network output vars
        net_output = lasagne.layers.get_output(self.l_out, self.states_for_output / 255.0)
        net_output_statetp1 = lasagne.layers.get_output(self.l_out, self.states_tp1 / 255.0)
        net_output_statetp1 = theano.gradient.disconnected_grad(net_output_statetp1)
        net_output_training = lasagne.layers.get_output(self.l_out, self.states_for_training / 255.0)

        # setup qlearning values and loss
        est_rew_tp1 = (1-self.terminals) * training_parms.get('discount') * T.max(net_output_statetp1, axis=1)
        rewards = self.rewards + est_rew_tp1
        diff = rewards - net_output_training[T.arange(minibatch), self.actions]
        loss = T.mean(diff**2)
        # # get layaer parms
        params = lasagne.layers.get_all_params(self.l_out)
        rms_update = lasagne.updates.rmsprop(loss, params, training_parms.get('learning_rate'),
                                             rho=training_parms.get('rms_decay'),
                                             epsilon=training_parms.get('rms_epsilon'))

        self._train_optimized = theano.function([], loss, updates=rms_update)
        self._get_output = theano.function([], outputs=net_output)
        self.get_hid1_act = theano.function([self.l_in.input_var], outputs=lasagne.layers.get_output(self.l_hid1))
        self.get_hid2_act = theano.function([self.l_in.input_var], outputs=lasagne.layers.get_output(self.l_hid2))

    def train(self, states, actions, rewards, state_tp1s, terminal):
        self.states_for_training.set_value(states)
        self.actions.set_value(actions)
        self.rewards.set_value(rewards)
        self.states_tp1.set_value(state_tp1s)
        self.terminals.set_value(terminal)
        return self._train_optimized()

    def get_output(self, state):
        self.states_for_output.set_value(state)
        return self._get_output()[0]

    def load(self, filename):
        import lasagne
        import pickle
        with open(filename, 'rb') as in_file:
            layer_params = pickle.load(in_file)
            lasagne.layers.set_all_param_values(self.l_out, layer_params)

    def save(self, filename):
        import lasagne
        import pickle
        with open(filename + '.pkl', 'wb') as out_file:
            pickle.dump(lasagne.layers.get_all_param_values(self.l_out), out_file)
